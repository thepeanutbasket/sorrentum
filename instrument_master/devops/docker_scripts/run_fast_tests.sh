#!/usr/bin/env bash

set -e

OPTS="-vv -rpa"
#OPTS="$OPTS --log-cli-level=INFO"

SKIPPED_TESTS="not slow and \
    not superslow and \
    not broken_deps and \
    not need_data_dir and \
    not not_docker"

TEST_DIR="instrument_master"

# Run tests.
cmd="pytest ${OPTS} -m '${SKIPPED_TESTS}' ${TEST_DIR}"
echo "> cmd=$cmd"
eval $cmd
