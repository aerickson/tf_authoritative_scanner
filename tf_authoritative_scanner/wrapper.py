import sys
import os
import argparse

from tf_authoritative_scanner.scanner import TFAuthoritativeScanner
from tf_authoritative_scanner.util import _get_version, remove_leading_trailing_newline


class Wrapper:
    def __init__(self, args):
        pass

    def run_tfas_and_terraform(self, args):
        scanner = TFAuthoritativeScanner(include_dotdirs=False, verbosity=0)
        result = scanner.check_paths_for_authoritative_resources(".")
        tf_cmd = "terraform"
        full_cmd_list = [tf_cmd] + args
        full_cmd_str = f"{tf_cmd} {' '.join(args)}"
        if result["authoritative_files_found"]:
            count = result["authoritative_files_count"]
            print(f"Authoritative files found ({count}). Run `tfas .` to view results.")
            print(f"Not running `{full_cmd_str}`.")
            sys.exit(1)

        # If no authoritative files found, continue with `terraform`.

        print(f"No authoritative files found. Continuing with `{full_cmd_str}`...")
        print()

        # Replace the current process with `terraform` command
        os.execvp(full_cmd_list[0], full_cmd_list)

    def print_tfast_banner(self):
        print(
            remove_leading_trailing_newline(
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
        )

    def is_terraform_directory(self):
        return any(file.endswith(".tf") for file in os.listdir("."))


def main():
    parser = argparse.ArgumentParser(
        description="`tfas` Terraform wrapper. Ensures Terraform code in the current directory doesn't have any authoritative resources before running `terraform`."
    )
    parser.add_argument("terraform_args", nargs=argparse.REMAINDER, help="Arguments to pass to `terraform`")
    parser.add_argument(
        "--version",
        action="version",
        version=_get_version("__init__.py"),
    )
    parser.add_argument("--no-ascii-art", "-A", action="store_true", help="Do not print ASCII art")
    args = parser.parse_args()
    w = Wrapper(args)

    if not args.no_ascii_art:
        w.print_tfast_banner()
    if not w.is_terraform_directory():
        print("No Terraform files found in the current directory. Please ensure you're in a directory with .tf files.")
        # parser.print_help()
        sys.exit(1)
    w.run_tfas_and_terraform(args.terraform_args)
