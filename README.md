# tf_authoritative_scanner

## Overview

`tfas` performs static analysis on Terraform files to detect the presence of authoritative resources (currently only GCP Terraform resources, but pull requests welcome). It scans a specified directory (and optionally hidden directories to inspect 3rd party modules) for Terraform configuration files (.tf) and identifies lines containing these authoritative resources.

If such resources are found, it reports their file paths and line numbers, and exits with a non-zero status unless the lines are marked with an exception comment (`# terraform_authoritative_scanner_ok` inline or on the line before).

## Background and Comments

Authoritative Terraform resources are extremely dangerous because:
- they can and will remove non-Terraform managed resources
- they won't mention actions in `terraform plan` output

Authoritative Terraform resources should be used when setting up new infrastructure. It's desirable in this state to wipe out anything not in Terraform.

If you're working with existing infrastructure they should only be used once all infrastructure is being managed by Terraform.

## Usage

### Pre-Commit

Add the following to your `.pre-commit-config.yaml` file.

```
- repo: https://github.com/aerickson/tf_authoritative_scanner.git
  rev: v1.0.4
  hooks:
    - id: tfas
```

Stage the file then run `pre-commit autoupdate` to grab the latest release.

### Interactively

#### Normal Usage

```bash
$ poetry build
$ pip install dist/tf_authoritative_scanner-1.0.X-py3-none-any.whl

$ tfas -h
# help output
...
$ tfas ~/git/terraform_repo/
AUTHORITATIVE: ~/git/terraform_repo/project_red/iam.tf:10: resource "google_project_iam_binding" "compute_admin" {
AUTHORITATIVE: ~/git/terraform_repo/project_blue/iam.tf:10: resource "google_project_iam_binding" "compute_admin" {
FAIL: 2 of 232 scanned files are authoritative.
$ echo $?
1
$
```

#### Development

```bash
$ poetry shell
$ poetry install
$ tfas
```

## Known Issues

- resource names that have authoritative resource will alert
  - use an exception comment for now

## Development

### Version Bumping

```bash
# poetry install via shell script
pipx inject poetry poetry-bumpversion
# poetry installed via pipx
poetry self add poetry-bumpversion

poetry version -h

# increment minor version
poetry version patch
```

### TODO

- publish to pypi
- more advanced detection
  - simple substring is used now, check for `resource "BLAH"` or `resource 'BLAH'`
  - don't false trigger, see 'Known Issues' above
- add an option to show the list of authoritative resources checked for

## Relevant Links

- mentions the danger of authoritative resources and other reasons not to use
  - https://fabianlee.org/2021/02/05/terraform-using-non-authoritative-resources-to-avoid-iam-membership-dependency-web/
- open GH issue about the danger of authoritative resources
  - https://github.com/hashicorp/terraform-provider-google/issues/8354
