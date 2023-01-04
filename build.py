import os.path
from subprocess import Popen, PIPE
from constants import BASE_PATH, SERVICE_BASE_PATH, BIN_PATH
from os.path import realpath, exists


def get_all_services():
    services = []
    for service in os.listdir(f'{BASE_PATH}/{SERVICE_BASE_PATH}'):
        services.append(service)
    return sorted(services)


def build_bin(service=None, force=False):
    service_path = f'{SERVICE_BASE_PATH}/{service}'
    bin_path = f'./{BIN_PATH}/{service}.test'

    if exists(bin_path) and not force:
        print(f'Binary already exists for {service}')
        return
    print(f'Building {service}...')

    cmd = [
        'go',
        'test',
        '-c',
        service_path,
        '-o',
        bin_path,
    ]

    proc = Popen(
        cmd,
        stdout=PIPE,
        stderr=PIPE,
        universal_newlines=True,
        cwd=realpath(BASE_PATH)
    )
    stdout, stderr = proc.communicate()
    proc.terminate()
    if stdout:
        print(f'stdout: {stdout}')
    if stderr:
        print(f'stderr: {stderr}')

    if exists(bin_path):
        os.chmod(bin_path, 0o755)
