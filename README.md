Terraform vs LocalStack
=======================

This repository contains scripts and CI configurations to to run the Terraform Acceptance test suite of the AWS provider against LocalStack

## Utilities

Some utilities for local development:

* `bin/list-tests [--all]`: list the available tests by parsing the go test files.
* `bin/install-aws-test` creates the binary for running the test suite (and installs it into `$HOME/.cache/localstack/aws.test`. requires go 1.16
* `bin/run-tests [test]` run a specific test. this installs and runs localstack in a background process. add the flag `-t` to test against an already running localstack instance.

## Finding and running tests

After running `bin/install-aws-test`, use `bin/run-tests [OPTIONS...] [TESTS...]` to run individual tests or entire test suites.

Here are some examples:

* `bin/run-tests TestAccAWSAPIGatewayResource`
* `bin/run-tests -t TestAccAWSAPIGatewayResource`: same as above, but does not start localstack
* `bin/run-tests TestAccAWSAPIGateway`: runs all tests that match `TestAccAWSAPIGateway` (run `bin/list-tests TestAccAWSAPIGateway` to see which ones will be executed)
* `bin/run-tests -e TestAccAWSAPIGatewayV2 TestAccAWSAPIGateway`: same as above, but excludes all tests that match `TestAccAWSAPIGatewayV2`.
* `bin/run-tests -i localstack-tests.incl.txt`: runs all tests listed in the text file

You can use `bin/list-tests` with the same parameters to see which tests will be executed,
or to find specific tests based on patterns.

For example:

```
 % bin/list-tests Queue
TestAccAWSBatchJobQueue
TestAccAWSGameliftGameSessionQueue
TestAccAWSMediaConvertQueue
TestAccAWSSQSQueue
TestAccAWSSQSQueuePolicy
TestAccDataSourceAwsBatchJobQueue
TestAccDataSourceAwsSqsQueue
```

or

```
 % bin/list-tests "Data.*Queue"
TestAccDataSourceAwsBatchJobQueue
TestAccDataSourceAwsSqsQueue
```

## Generating the test reports

Test logs are aggregated into `build/tests/*.log`, the command `bin/create-report` will create junit-like xml reports.
These can then be rendered into html using `bin/create-report-html`, which also creates a summary page in `build/report.html`.
For rendering html, you need `junit2html`.

## Travis config

### Build cache

The Travis-CI worker caches the built `aws.test` binary across builds.
The first build may therefore take a while.
