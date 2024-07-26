#!/usr/bin/env python3

import os
import re
import sys
import argparse

VERSION = "1.0.0"  # Define the version constant

class TFAuthoritativeScanner:
    authoritative_resources = [
        "google_project_iam_binding",
        "google_folder_iam_binding",
        "google_organization_iam_binding"
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
        "google_folder_iam_policy",
        "google_organization_iam_member",
        "google_organization_iam_policy",
        "google_container_cluster",
        "google_pubsub_topic",
        "google_cloud_run_service"
    ]

    exception_comment_pattern = re.compile(r"#\s*terraform_authoritative_scanner_ok")

    def __init__(self, directory, include_dotdirs, verbose=False):
        self.directory = directory
        self.include_dotdirs = include_dotdirs
        self.verbose = verbose

    def check_file_for_authoritative_resources(self, file_path):
        with open(file_path, 'r') as file:
            lines = file.readlines()

        authoritative_lines = []
        previous_line = ""
        for line_number, line in enumerate(lines, start=1):
            stripped_line = line.strip()
            # Ignore comment lines
            if stripped_line.startswith("#"):
                previous_line = stripped_line
                continue
            # Check if the line contains any authoritative resource and is not excepted
            if any(resource in line for resource in self.authoritative_resources):
                if not self.exception_comment_pattern.search(line) and not self.exception_comment_pattern.search(previous_line):
                    authoritative_lines.append((line_number, stripped_line))
            previous_line = stripped_line

        return authoritative_lines

    def check_directory_for_authoritative_resources(self):
        all_authoritative_lines = []
        total_files = 0
        for root, dirs, files in os.walk(self.directory):
            if not self.include_dotdirs:
                # Exclude directories starting with '.'
                dirs[:] = [d for d in dirs if not d.startswith('.')]
            for file in files:
                if file.endswith(".tf"):
                    total_files += 1
                    file_path = os.path.join(root, file)
                    authoritative_lines = self.check_file_for_authoritative_resources(file_path)
                    if authoritative_lines:
                        all_authoritative_lines.append((file_path, authoritative_lines))
        return all_authoritative_lines, total_files

    def run(self):
        all_authoritative_lines, total_files = self.check_directory_for_authoritative_resources()
        if all_authoritative_lines:
            if self.verbose:
                for file_path, lines in all_authoritative_lines:
                    for line_number, line in lines:
                        print(f"Authoritative resource found in {file_path} at line {line_number}: {line}")
            else:
                authoritative_files = len(all_authoritative_lines)
                print(f"{authoritative_files} of {total_files} scanned files are authoritative.")
            sys.exit(1)
        else:
            # print(f"No authoritative resources found in {total_files} scanned files.")
            authoritative_files = len(all_authoritative_lines)
            print(f"{authoritative_files} of {total_files} scanned files are authoritative.")
            sys.exit(0)

def main():
    parser = argparse.ArgumentParser(description="Static analysis of Terraform files for authoritative GCP resources.")
    parser.add_argument("directory", help="Directory path containing Terraform files")
    parser.add_argument("-i", "--include-dotdirs", action="store_true", help="Include directories starting with a dot")
    parser.add_argument("--version", action="version", version=f"%(prog)s {VERSION}", help="Show program's version number and exit")
    parser.add_argument("-v", "--verbose", action="store_true", help="Show detailed output of authoritative resource lines")
    args = parser.parse_args()

    if not os.path.exists(args.directory):
        print(f"Error: The directory {args.directory} does not exist.", file=sys.stderr)
        sys.exit(1)

    scanner = TFAuthoritativeScanner(args.directory, args.include_dotdirs, args.verbose)
    scanner.run()

if __name__ == "__main__":
    main()