#!/usr/bin/env python3

import os
import re
import sys
import argparse

VERSION = "1.0.2"


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

    def __init__(self, include_dotdirs, verbosity=0):
        self.include_dotdirs = include_dotdirs
        self.verbosity = verbosity

    def check_file_for_authoritative_resources(self, file_path):
        with open(file_path, "r") as file:
            lines = file.readlines()

        authoritative_lines = []
        excepted_lines = []
        authoritative = False
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
                    authoritative = True
                else:
                    excepted_lines.append({"line_number": line_number, "line": stripped_line})
            previous_line = stripped_line

        return {
            "file_path": file_path,
            "authoritative": authoritative,
            "authoritative_lines": authoritative_lines,
            "excepted_lines": excepted_lines,
        }

    def _scan_directory(self, directory):
        for root, dirs, files in os.walk(directory):
            if not self.include_dotdirs:
                dirs[:] = [d for d in dirs if not d.startswith(".")]
            for file in files:
                if file.endswith(".tf"):
                    yield os.path.join(root, file)

    def check_paths_for_authoritative_resources(self, directory):
        results = []
        total_files = 0
        for path in directory:
            if os.path.isdir(path):
                files = self._scan_directory(path)
            else:
                files = [path]

            for file_path in files:
                total_files += 1
                file_entry = self.check_file_for_authoritative_resources(file_path)
                results.append(file_entry)
        return {"files_scanned": total_files, "results": results}

    def run(self, paths):
        total_files = 0
        results = []
        authoritative_files_found = 0

        call_result = self.check_paths_for_authoritative_resources(paths)
        results = call_result.get("results")
        total_files = call_result.get("files_scanned")

        for file_entry in results:
            file_path = file_entry["file_path"]

            if file_entry["authoritative"]:
                authoritative_files_found += 1
                if self.verbosity:
                    authoritative_lines = file_entry["authoritative_lines"]
                    for item in authoritative_lines:
                        line_number = item["line_number"]
                        line = item["line"]
                        print(f"AUTHORITATIVE: {file_path}:{line_number}: {line}")
            elif file_entry["excepted_lines"]:
                if self.verbosity:
                    excepted_lines = file_entry["excepted_lines"]
                    for item in excepted_lines:
                        line_number = item["line_number"]
                        line = item["line"]
                        print(f"EXCEPTED: {file_path}:{line_number}: {line}")
            else:
                if self.verbosity:
                    print(f"OK: {file_path}")

        if authoritative_files_found > 0:
            print(f"FAIL: {authoritative_files_found} of {total_files} scanned files are authoritative.")
            sys.exit(1)
        else:
            print(f"PASS: {authoritative_files_found} of {total_files} scanned files are authoritative.")
            sys.exit(0)


def _verify_paths(paths):
    for path in paths:
        if not os.path.exists(path):
            print(f"Error: The path '{path}' does not exist.")
            sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Static analysis of Terraform files for authoritative GCP resources.")
    parser.add_argument("paths", metavar="path", type=str, nargs="+", help="File or directory to scan")
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

    _verify_paths(args.paths)
    scanner = TFAuthoritativeScanner(args.include_dotdirs, args.verbose)
    scanner.run(args.paths)


if __name__ == "__main__":
    main()
