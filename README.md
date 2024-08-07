# tf_authoritative_scanner


## Overview

`tfas` performs static analysis on Terraform files to detect the presence of Terraformauthoritative resources (ARs). It scans a specified directory (and optionally hidden directories to inspect modules) for Terraform configuration files (.tf) and identifies lines containing these ARs.

`tfast` is a Terraform porcelain (e.g. `tfast plan`). It will only run the specified Terraform command if `tfas` doesn't find any ARs.

### Background and Comments

Authoritative Terraform resources are extremely dangerous because:
- they can and will remove non-Terraform managed resources
- they won't mention actions in `terraform plan` output

Authoritative Terraform resources should be used when setting up new infrastructure. It's desirable in this state to wipe out anything not in Terraform.

If you're working with existing infrastructure they should only be used once all infrastructure is being managed by Terraform.


## Usage


### Authoritative Resource Exceptions

If you want to allow a specific usage of an authorized resource, add a comment with `terraform_authoritative_scanner_ok` and `tfas` won't alert on it. The comment can be on the line before the authoritative resource or inline.

```bash
    # terraform_authoritative_scanner_ok
    resource "google_project_iam_binding" "binding" {
      ...
    }

    resource "google_project_iam_binding" "binding2" {  # terraform_authoritative_scanner_ok
      ...
    }
```

### Installation

```bash
$ poetry build
$ pipx install dist/tf_authoritative_scanner-1.0.X-py3-none-any.whl
```


### `tfas`


#### Running via Pre-Commit

Add the following to your `.pre-commit-config.yaml` file.

```
- repo: https://github.com/aerickson/tf_authoritative_scanner.git
  rev: v1.0.4
  hooks:
    - id: tfas
```

Stage the file then run `pre-commit autoupdate` to grab the latest release.


#### Running Interactively

```bash
$ tfas -h
...

$ tfas ~/git/terraform_repo/
AUTHORITATIVE: ~/git/terraform_repo/project_red/iam.tf:10: resource "google_project_iam_binding" "compute_admin" {
AUTHORITATIVE: ~/git/terraform_repo/project_blue/iam.tf:10: resource "google_project_iam_binding" "compute_admin" {
FAIL: 2 of 232 scanned files are authoritative.
$ echo $?
1
$
```


### `tfast`

```bash
cd ~/git/your_terraform_repo
tfast plan
tfast apply
```





## Development

### Testing Changes

```bash
$ poetry shell
$ poetry install
# make changes to the code
$ tfas
$ tfast
```


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
- surface confidence in verbose mode
- add an option to show the list of authoritative resources checked for
- provide links to documentation when an authoritative resource is detected


## Relevant Links

- mentions the danger of authoritative resources and other reasons not to use
  - https://fabianlee.org/2021/02/05/terraform-using-non-authoritative-resources-to-avoid-iam-membership-dependency-web/
- open GH issue about the danger of authoritative resources
  - https://github.com/hashicorp/terraform-provider-google/issues/8354
