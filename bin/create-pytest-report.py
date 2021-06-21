#!/usr/bin/python3

import glob
import os

prefixes = {
    'go': '[ltt.gotest]',
    'lst': '[ltt.localstack]',
    'runner': '[ltt.runner]'
}


def strip_special_chars(line):
    # remove special characters, convert to str
    if not isinstance(line, bytes):
        line = line.replace('\x1b', '').encode('utf-8')
    return line.decode('utf-8', 'ignore')


class TestCase:
    def __init__(self, suite, test):
        self.suite = suite
        self.test = test
        self.lines = list()
        self.duration = 0
        self.result = None


class RunnerLogParser:
    def __init__(self, suite):
        self.suite = suite
        self.tests = dict()
        self.active_test = None
        self.collecting = False

    def parse_duration(self, fragment):
        seconds = fragment[1:-2]  # (0.00s) -> 0.00
        return float(seconds)

    def add_line(self, src, line):
        tests = self.tests
        suite = self.suite

        line = strip_special_chars(line)

        output = line[len(prefixes[src]) + 1:]

        if src == 'runner':
            if output.startswith('starting'):
                if output.strip().split()[-1] == suite:
                    self.collecting = True

            if output.startswith('completed'):
                if output.strip().split()[-1] == suite:
                    self.collecting = False

        if not self.collecting:
            return

        if src == 'go':
            if output.startswith('=== RUN'):
                _, _, test = output.split()
                if test not in tests:
                    tests[test] = TestCase(suite, test)

                self.active_test = test
                return

            elif output.startswith('=== PAUSE'):
                _, _, test = output.split()
                self.active_test = None
                return

            elif output.startswith('=== CONT'):
                _, _, test = output.split()
                self.active_test = test
                return

            elif output.strip().startswith('--- PASS'):
                _, _, test, duration = output.split()
                self.active_test = None
                tests[test].result = 'passed'
                tests[test].duration = self.parse_duration(duration)
                return

            elif output.strip().startswith('--- SKIP'):
                _, _, test, duration = output.split()
                self.active_test = None
                tests[test].result = 'skipped'
                tests[test].duration = self.parse_duration(duration)
                return

            elif output.strip().startswith('--- FAIL'):
                _, _, test, duration = output.split()
                self.active_test = None
                tests[test].result = 'failed'
                tests[test].duration = self.parse_duration(duration)
                return

            elif output.strip().startswith('--- ERROR'):
                _, _, test, duration = output.split()
                self.active_test = None
                tests[test].result = 'errored'
                tests[test].duration = self.parse_duration(duration)
                return

        if self.active_test:
            tests[self.active_test].lines.append(line)


def parse(suite, lines):
    parser = RunnerLogParser(suite)

    for line in lines:
        for src, prefix in prefixes.items():
            if line.startswith(prefix):
                parser.add_line(src, line)

    for test in parser.tests.values():
        if test.result is None:
            test.result = 'errored'
            test.duration = 0.

    return parser


def parser_to_xml(parser):
    testsuite = {
        'name': parser.suite,
        'time': 0,
        'errors': 0,
        'failures': 0,
        'skipped': 0,
        'tests': 0,
    }

    def find_fail_message(testcase: TestCase):
        for line in testcase.lines:
            if not line.startswith('[ltt.gotest]'):
                continue

            if 'Step' in line and '.go' in line and 'error' in line:
                return line.strip()

        return 'failure'

    def test_to_junit_dict(testcase: TestCase):
        d = {
            'name': testcase.test,
            'classname': testcase.test.split('/')[0],
            'time': "%.2f" % testcase.duration,
        }

        testsuite['tests'] += 1
        testsuite['time'] += testcase.duration

        if testcase.result == 'errored':
            d['error'] = {
                'type': 'error',
                '__CDATA__': ''.join(testcase.lines)
            }
            testsuite['errors'] += 1

        if testcase.result == 'failed':
            d['failure'] = {
                'type': 'failure',
                'message': escape(find_fail_message(testcase)),
                '__CDATA__': ''.join(testcase.lines)
            }
            testsuite['failures'] += 1

        if testcase.result == 'skipped':
            d['skipped'] = {}
            testsuite['skipped'] += 1

        return d

    testcases = [dict2xml(test_to_junit_dict(t), 'testcase') for t in parser.tests.values()]

    testsuite['properties'] = [{
        'property': {'name': 'test-runner', 'value': 'localstack-terraform-test'}
    }]

    testsuite['__XML__'] = testcases

    return dict2xml(testsuite, 'testsuite')


def escape(s):
    s = s.replace("&", "&amp;")
    s = s.replace("<", "&lt;")
    s = s.replace(">", "&gt;")
    s = s.replace("\"", "&quot;")
    s = s.replace("'", "&apos;")
    return s


def dict2xml(d, root_node=None):
    wrap          =     False if None == root_node or isinstance(d, list) else True
    root          = 'objects' if None == root_node else root_node
    root_singular = root[:-1] if 's' == root[-1] and None == root_node else root
    xml           = ''
    children      = []

    if isinstance(d, dict):
        for key, value in dict.items(d):
            if key == '__CDATA__':
                children.append('<![CDATA[' + value + ']]>')
            elif key.startswith('__XML__'):
                if isinstance(value, list):
                    children.append('\n'.join(value))
                else:
                    children.append(value)
            elif isinstance(value, dict):
                children.append(dict2xml(value, key))
            elif isinstance(value, list):
                children.append(dict2xml(value, key))
            else:
                xml = xml + ' ' + key + '="' + str(value) + '"'
    else:
        for value in d:
            children.append(dict2xml(value, root_singular))

    end_tag = '>' if 0 < len(children) else '/>'

    if wrap or isinstance(d, dict):
        xml = '<' + root + xml + end_tag

    if 0 < len(children):
        for child in children:
            xml = xml + child

        if wrap or isinstance(d, dict):
            xml = xml + '</' + root + '>'

    return xml


def main():
    for f in glob.glob('build/tests/*.log'):
        with open(f, 'rb') as fd:
            lines = fd.readlines()

        lines = [strip_special_chars(line) for line in lines]
        suite = os.path.basename(f)[:-4]  # strip `.log`
        parser = parse(suite, lines)

        f_xml = f[:-4] + '.xml'
        d = os.path.dirname(f_xml)
        f = os.path.basename(f_xml)

        f_xml = os.path.join(d, 'TEST-' + f)

        with open(f_xml, 'w') as fd:
            print(f_xml)
            fd.writelines(parser_to_xml(parser))

if __name__ == '__main__':
    main()
