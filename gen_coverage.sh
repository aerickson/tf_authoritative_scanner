#!/usr/bin/env bash

set -e

# Check if the first argument is provided
if [ -z "$1" ]; then
    report_format="term-missing"
else
    report_format="$1"
fi

pytest --cov tf_authoritative_scanner --cov-report=${report_format} -vvv
