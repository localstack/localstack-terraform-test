Terraform vs LocalStack
=======================

This repository contains scripts and CI configurations to to run the Terraform Acceptance test suite of the AWS provider against LocalStack

## Utilities

Some utilities for local development:

* `bin/list-tests [--all]`: list the available tests by parsing the go test files.
* `bin/install-aws-test` creates the binary for running the test suite (and installs it into `$HOME/.cache/localstack/aws.test`. requires go 1.16
* `bin/run-tests [test]` run a specific test. this installs and runs localstack in a background process

### Generating the test report

The `build/test.log` can be transformed into a JUnit XML document using `go-junit-report`, which can then be used for other visualization tools.
You need go and can install it with `go get`.

    go get -u github.com/jstemmer/go-junit-report

Then run

    bin/create-report

## Running locally

TODO

## Travis config

### Build cache

The Travis-CI worker caches the built `aws.test` binary across builds.
The first build may therefore take a while.
