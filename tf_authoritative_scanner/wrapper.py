import sys
import os
import argparse

from tf_authoritative_scanner.scanner import TFAuthoritativeScanner
from tf_authoritative_scanner.util import _get_version


def run_tfas_and_terraform(args):
    # command_list = ["tfas", "."]
    # try:
    #     _result = subprocess.run(command_list, check=True)
    # except subprocess.CalledProcessError as e:
    #     print()
    #     print(f"Error running `{' '.join(command_list)}`. Not running `terraform`.", file=sys.stderr)
    #     sys.exit(e.returncode)

    scanner = TFAuthoritativeScanner(include_dotdirs=False, verbosity=0)
    result = scanner.check_paths_for_authoritative_resources(".")
    if result["authoritative_files_found"]:
        print("Authoritative files found. Not running `terraform`.")
        sys.exit(1)

    # import pprint; pprint.pprint(result)

    # sys.exit(0)

    # If `tfas .` exits with 0, continue with `terraform`
    terraform_command = ["terraform"] + args

    print(f"No authoritative files found. Continuing with `{' '.join(terraform_command)}`...")
    print()

    # Replace the current process with `terraform` command
    os.execvp("terraform", terraform_command)


def print_tfast_banner():
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


def is_terraform_directory():
    return any(file.endswith(".tf") for file in os.listdir("."))


def main():
    print("foooofoooo")

    parser = argparse.ArgumentParser(
        description="`tfas` Terraform wrapper. Ensures Terraform code in the current directory doesn't have any authoritative resources before running `terraform`."
    )
    parser.add_argument("terraform_args", nargs=argparse.REMAINDER, help="Arguments to pass to `terraform`")
    parser.add_argument(
        "--version",
        "-v",
        action="version",
        version=_get_version("__init__.py"),
    )
    args = parser.parse_args()

    # print_tfast_banner()

    if not is_terraform_directory():
        print("No Terraform files found in the current directory. Please ensure you're in a directory with .tf files.")
        # parser.print_help()
        sys.exit(1)

    run_tfas_and_terraform(args.terraform_args)
