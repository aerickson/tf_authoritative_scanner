#!/usr/bin/env python3

import os
import re
import sys
import argparse

VERSION = "1.0.0"  # Define the version constant


class TFAuthoritativeScanner:
    authoritative_resources = [
        "google_project_iam_policy",
        "google_project_iam_binding",
        "google_folder_iam_binding",
        "google_organization_iam_binding",
        "google_folder_iam_policy",
        "google_organization_iam_policy",
        "google_storage_bucket_iam_policy",
        "google_storage_bucket_iam_binding",
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

    def __init__(self, directory, include_dotdirs, verbosity=0):
        self.directory = directory
        self.include_dotdirs = include_dotdirs
        self.verbosity = verbosity

    def check_file_for_authoritative_resources(self, file_path):
        with open(file_path, "r") as file:
            lines = file.readlines()

        authoritative_lines = []
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
                    authoritative_lines.append((line_number, stripped_line))
                    non_authoritative = False
            previous_line = stripped_line

        return authoritative_lines, non_authoritative

    def check_directory_for_authoritative_resources(self):
        all_authoritative_lines = []
        non_authoritative_files = []
        total_files = 0
        for root, dirs, files in os.walk(self.directory):
            if not self.include_dotdirs:
                # Exclude directories starting with '.'
                dirs[:] = [d for d in dirs if not d.startswith(".")]
            for file in files:
                if file.endswith(".tf"):
                    total_files += 1
                    file_path = os.path.join(root, file)
                    authoritative_lines, non_authoritative = self.check_file_for_authoritative_resources(file_path)
                    if authoritative_lines:
                        all_authoritative_lines.append((file_path, authoritative_lines))
                    if self.verbosity >= 2 and non_authoritative:
                        non_authoritative_files.append(file_path)

        return all_authoritative_lines, total_files, non_authoritative_files

    def run(self):
        all_authoritative_lines, total_files, non_authoritative_files = (
            self.check_directory_for_authoritative_resources()
        )
        if self.verbosity >= 2:
            for file_path in non_authoritative_files:
                print(f"OK: {file_path}")
        if all_authoritative_lines:
            if self.verbosity >= 1:
                for file_path, lines in all_authoritative_lines:
                    for line_number, line in lines:
                        print(f"AUTHORITATIVE: {file_path}:{line_number}: {line}")
            authoritative_files = len(all_authoritative_lines)
            print(f"ERROR: {authoritative_files} of {total_files} scanned files are authoritative.")
            sys.exit(1)
        else:
            authoritative_files = len(all_authoritative_lines)
            print(f"PASS: {authoritative_files} of {total_files} scanned files are authoritative.")
            sys.exit(0)


def main():
    parser = argparse.ArgumentParser(description="Static analysis of Terraform files for authoritative GCP resources.")
    parser.add_argument("directory", help="Directory path containing Terraform files")
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

    if not os.path.exists(args.directory):
        print(f"Error: The directory {args.directory} does not exist.", file=sys.stderr)
        sys.exit(1)

    scanner = TFAuthoritativeScanner(args.directory, args.include_dotdirs, args.verbose)
    scanner.run()


if __name__ == "__main__":
    main()
