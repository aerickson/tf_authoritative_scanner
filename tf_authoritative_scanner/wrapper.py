import subprocess
import sys
import os
import argparse

from tf_authoritative_scanner.util import _get_version


def run_tfas_and_terraform(args):
    command_list = ["tfas", "."]
    try:
        _result = subprocess.run(command_list, check=True)
    except subprocess.CalledProcessError as e:
        print()
        print(f"Error running `{' '.join(command_list)}`. Not running `terraform`.", file=sys.stderr)
        sys.exit(e.returncode)

    # If `tfas .` exits with 0, continue with `terraform`
    terraform_command = ["terraform"] + args

    # Replace the current process with `terraform` command
    os.execvp("terraform", terraform_command)


def print_ascii_art_banner():
    print(
        r"""

 __       ___                 __
/\ \__  /'___\               /\ \__
\ \ ,_\/\ \__/   __      ____\ \ ,_\
 \ \ \/\ \ ,__\/'__`\   /',__\\ \ \/
  \ \ \_\ \ \_/\ \L\.\_/\__, `\\ \ \_
   \ \__\\ \_\\ \__/.\_\/\____/ \ \__\
    \/__/ \/_/ \/__/\/_/\/___/   \/__/

"""
    )


def main():
    parser = argparse.ArgumentParser(description="Run `tfas .` and continue with `terraform` if successful.")
    parser.add_argument("terraform_args", nargs=argparse.REMAINDER, help="Arguments to pass to `terraform`")
    parser.add_argument(
        "--version",
        "-v",
        action="version",
        version=_get_version("__init__.py"),
    )
    args = parser.parse_args()

    print_ascii_art_banner()
    # TODO: detect if we're in a terraform directory and if not show usage/help
    run_tfas_and_terraform(args.terraform_args)
