"""
Test fixture that spins up localstack and is shared across test modules, see:
https://docs.pytest.org/en/6.2.x/fixture.html#conftest-py-sharing-fixtures-across-multiple-files

It is thread/process safe to run with pytest-parallel.
"""
import contextlib
import io
import logging
import multiprocessing as mp
import os
import sys
import threading
from contextlib import redirect_stdout, redirect_stderr

import pytest

logger = logging.getLogger(__name__)

fixture_mutex = mp.Lock()  # mutex for getting the localstack_runtime fixture, which can trigger the startup
localstack_started = mp.Event()  # event indicating whether localstack has been started
localstack_stop = mp.Event()  # event that can be triggered to stop localstack
localstack_stopped = mp.Event()  # event indicating that localstack has been stopped
startup_monitor_event = mp.Event()  # event that can be triggered to start localstack


@pytest.hookimpl()
def pytest_configure(config):
    if should_start_localstack_embedded():
        _start_monitor()


@pytest.hookimpl()
def pytest_unconfigure(config):
    _trigger_stop()


def should_start_localstack_embedded():
    return os.environ.get("START_EMBEDDED") in ["1", "true"]


def startup_monitor() -> None:
    logger.info('waiting on localstack_start signal')
    startup_monitor_event.wait()

    if localstack_stop.is_set():
        logger.info('ending startup_monitor')
        return

    logger.info('running localstack')
    run_and_capture_localstack()


def _start_monitor():
    threading.Thread(target=startup_monitor).start()


def _trigger_stop():
    localstack_stop.set()
    startup_monitor_event.set()


def run_localstack():
    from localstack.constants import ENV_INTERNAL_TEST_RUN
    from localstack.services import infra
    os.environ[ENV_INTERNAL_TEST_RUN] = '1'

    def watchdog():
        logger.info('waiting stop event')
        localstack_stop.wait()
        logger.info('stopping infra')
        infra.stop_infra()

    monitor = threading.Thread(target=watchdog)
    monitor.start()

    logger.info('starting localstack infrastructure')
    infra.start_infra(asynchronous=True)

    logger.info('waiting for infra to be ready')
    infra.INFRA_READY.wait()  # wait for infra to start (threading event)
    localstack_started.set()  # set conftest inter-process Event

    logger.info('waiting for shutdown')
    try:
        logger.info('waiting for watchdog to join')
        monitor.join()
    finally:
        logger.info('ok bye')
        localstack_stopped.set()


def run_and_capture_localstack():
    try:
        with capture_output() as buf:
            try:
                run_localstack()
            finally:
                buf.seek(0)
                val = buf.read()
    finally:
        logger.info('captured localstack output')
        try:
            for line in val.splitlines():
                logger.info('[localstack]: %s', line)
        except Exception as e:
            logger.exception('exception while replaying localstack output capture')


@pytest.fixture(scope='session', autouse=True)
def localstack_runtime():
    if not should_start_localstack_embedded():
        yield
        return

    fixture_mutex.acquire()
    if localstack_started.is_set():
        fixture_mutex.release()
        yield
        return

    try:
        startup_monitor_event.set()
        localstack_started.wait()
    finally:
        fixture_mutex.release()

    yield
    return


@contextlib.contextmanager
def capture_output(stdout=True, stderr=True):
    class StdBuffer(io.TextIOWrapper):
        def write(self, string):
            try:
                return super(StdBuffer, self).write(string)
            except TypeError:
                # redirect encoded byte strings directly to buffer
                return super(StdBuffer, self).buffer.write(string)

        def __str__(self):
            self.seek(0)
            return self.read()

    buf = StdBuffer(io.BytesIO(), encoding=sys.stdout.encoding)

    try:
        if stdout and stderr:
            with redirect_stdout(buf):
                with redirect_stderr(buf):
                    yield buf
        elif stdout:
            with redirect_stdout(buf):
                yield buf
        elif stderr:
            with redirect_stderr(buf):
                yield buf
        else:
            yield buf
    finally:
        buf.seek(0)
