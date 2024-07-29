#!/usr/bin/env python3

import os
import re
import sys
import argparse

VERSION = "1.0.0"  # Define the version constant


class TFAuthoritativeScanner:
    authoritative_resources = [
        "google_folder_iam_binding",
        "google_folder_iam_policy",
        "google_organization_iam_binding",
        "google_organization_iam_policy",
        "google_project_iam_audit_config",
        "google_project_iam_binding",
        "google_project_iam_policy",
        "google_storage_bucket_iam_binding",
        "google_storage_bucket_iam_policy",
    ]

    # less interesting / not verified authoritative resources
    _additional_resources = [
        "google_compute_instance",
        "google_storage_bucket",
        "google_sql_database_instance",
        "google_vpc_network",
        "google_compute_firewall",
        "google_compute_subnetwork",
        "google_folder_iam_member",
        "google_organization_iam_member",
        "google_container_cluster",
        "google_pubsub_topic",
        "google_cloud_run_service",
    ]

    exception_comment_pattern = re.compile(r"#\s*terraform_authoritative_scanner_ok")

    def __init__(self, file_or_directory, include_dotdirs, verbosity=0):
        self.file_or_directory = file_or_directory
        self.include_dotdirs = include_dotdirs
        self.verbosity = verbosity

    def check_file_for_authoritative_resources(self, file_path):
        with open(file_path, "r") as file:
            lines = file.readlines()

        authoritative_lines = []
        excepted_lines = []
        non_authoritative = True
        previous_line = ""
        for line_number, line in enumerate(lines, start=1):
            stripped_line = line.strip()
            # Ignore comment lines
            if stripped_line.startswith("#"):
                previous_line = stripped_line
                continue
            # Check if the line contains any authoritative resource and is not excepted
            if any(resource in line for resource in self.authoritative_resources):
                if not self.exception_comment_pattern.search(line) and not self.exception_comment_pattern.search(
                    previous_line
                ):
                    authoritative_lines.append({"line_number": line_number, "line": stripped_line})
                    non_authoritative = False
                else:
                    excepted_lines.append({"line_number": line_number, "line": stripped_line})
            previous_line = stripped_line

        return {
            # arrays of dicts
            "authoritative_lines": authoritative_lines,
            "excepted_lines": excepted_lines,
            # boolean
            "non_authoritative": non_authoritative,
        }

    def check_directory_for_authoritative_resources(self):
        all_authoritative_lines = []
        non_authoritative_files = []
        all_excluded_lines = []
        total_files = 0
        for root, dirs, files in os.walk(self.file_or_directory):
            if not self.include_dotdirs:
                # Exclude directories starting with '.'
                dirs[:] = [d for d in dirs if not d.startswith(".")]
            for file in files:
                if file.endswith(".tf"):
                    total_files += 1
                    file_path = os.path.join(root, file)
                    result = self.check_file_for_authoritative_resources(file_path)
                    authoritative_lines = result["authoritative_lines"]
                    non_authoritative = result["non_authoritative"]
                    excepted_lines = result["excepted_lines"]
                    if authoritative_lines:
                        all_authoritative_lines.append(
                            {"file_path": file_path, "authoritative_lines": authoritative_lines}
                        )
                    if excepted_lines:
                        all_excluded_lines.append({"file_path": file_path, "excepted_lines": excepted_lines})
                    if non_authoritative:
                        non_authoritative_files.append({"file_path": file_path})

        return {
            # arrays of dicts
            "all_excluded_lines": all_excluded_lines,
            "all_authoritative_lines": all_authoritative_lines,
            "non_authoritative_files": non_authoritative_files,
            # integer
            "total_files": total_files,
        }

    def run(self):
        if os.path.isdir(self.file_or_directory):
            result = self.check_directory_for_authoritative_resources()
            all_authoritative_lines = result["all_authoritative_lines"]
            total_files = result["total_files"]
            non_authoritative_files = result["non_authoritative_files"]
            excluded_files = result["all_excluded_lines"]
            # TODO: would be nicer to have a data structure keyed on file_path vs just put into different arrrays
            #   - ordering of output messages could be a bit odd (out of normal order)
            if self.verbosity:
                for item in excluded_files:
                    file_path = item["file_path"]
                    lines = item["excepted_lines"]
                    for item in lines:
                        line_number = item["line_number"]
                        line = item["line"]
                        print(f"EXCLUDED: {file_path}:{line_number}: {line}")
                for item in non_authoritative_files:
                    file_path = item["file_path"]
                    print(f"OK: {file_path}")
            if all_authoritative_lines:
                for item in all_authoritative_lines:
                    file_path = item["file_path"]
                    lines = item["authoritative_lines"]
                    for item in lines:
                        line_number = item["line_number"]
                        line = item["line"]
                        print(f"AUTHORITATIVE: {file_path}:{line_number}: {line}")
                authoritative_files = len(all_authoritative_lines)
                print(f"FAIL: {authoritative_files} of {total_files} scanned files are authoritative.")
                sys.exit(1)
            else:
                authoritative_files = len(all_authoritative_lines)
                print(f"PASS: {authoritative_files} of {total_files} scanned files are authoritative.")
                sys.exit(0)
        else:
            # a file was given
            raise SystemExit("Error: File mode doesn't work yet.")


def main():
    parser = argparse.ArgumentParser(description="Static analysis of Terraform files for authoritative GCP resources.")
    parser.add_argument("file_or_directory", help="the Terraform file or directory to scan")
    parser.add_argument(
        "-i",
        "--include-dotdirs",
        action="store_true",
        help="Include directories starting with a dot",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {VERSION}",
        help="Show program's version number and exit",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Increase verbosity level (can be used multiple times)",
    )
    args = parser.parse_args()

    # check if args.directory is a file, if it is, set args.directory to the parent directory

    if not os.path.exists(args.file_or_directory):
        print(f"Error: The directory {args.file_or_directory} does not exist.", file=sys.stderr)
        sys.exit(1)

    scanner = TFAuthoritativeScanner(args.file_or_directory, args.include_dotdirs, args.verbose)
    scanner.run()


if __name__ == "__main__":
    main()
