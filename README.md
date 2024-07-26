# tf_authoritative_scanner

## Overview

The TFAuthoritativeScanner tool performs static analysis on Terraform files to detect the presence of specific authoritative GCP resources. It scans the specified directory (and optionally includes hidden directories) for Terraform configuration files (.tf) and identifies lines containing these authoritative resources. If such resources are found, it reports their file paths and line numbers, and exits with a non-zero status unless the lines are marked with an exception comment (# terraform_authoritative_scanner_ok). This helps ensure that the configuration complies with specified infrastructure management policies.
