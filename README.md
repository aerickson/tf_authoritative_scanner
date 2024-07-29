# tf_authoritative_scanner

## Overview

`tfas` performs static analysis on Terraform files to detect the presence of specific authoritative GCP resources. It scans a specified directory (and optionally includes hidden directories) for Terraform configuration files (.tf) and identifies lines containing these authoritative resources.

If such resources are found, it reports their file paths and line numbers, and exits with a non-zero status unless the lines are marked with an exception comment (`# terraform_authoritative_scanner_ok` inline or on the line before).

Currently focuses on Google GCP Terraform authoritative resources (PRs welcome).

## Background

Authoritative Terraform resources are extremely dangerous because they will remove all non-Terraform managed resources and not mention it in `terraform plan` output.

Authoritative Terraform resources should be used when setting up new infrastructure, but when managing inherited infrastructure it's extremely dangerous.

## Known Issues

- resource names that have authoritative resource will alert
  - use an exception comment for now

## TODO

- more advanced detection
  - simple substring is used now, check for `resource "BLAH"` or `resource 'BLAH'`
  - don't false trigger, see 'Known Issues' above
- add an option to show the list of authoritative resources checked for

## Relevant Links

- mentions the danger of authoritative resources and other reasons not to use
  - https://fabianlee.org/2021/02/05/terraform-using-non-authoritative-resources-to-avoid-iam-membership-dependency-web/
- open GH issue about the danger of authoritative resources
  - https://github.com/hashicorp/terraform-provider-google/issues/8354
