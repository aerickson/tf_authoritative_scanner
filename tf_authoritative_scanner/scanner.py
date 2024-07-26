#!/usr/bin/env python3

import os
import re
import sys
import argparse

# Define authoritative GCP resources containing 'binding' in their name
authoritative_resources = [
    "google_project_iam_binding",
    "google_folder_iam_binding",
    "google_organization_iam_binding"
]

# Define other authoritative GCP resources (commented out for reference)
# "google_compute_instance",
# "google_storage_bucket",
# "google_sql_database_instance",
# "google_vpc_network",
# "google_compute_firewall",
# "google_compute_subnetwork",
# "google_project_iam_member",
# "google_project_iam_policy",
# "google_folder_iam_member",
# "google_folder_iam_policy",
# "google_organization_iam_member",
# "google_organization_iam_policy",
# "google_container_cluster",
# "google_pubsub_topic",
# "google_cloud_run_service"

# Define the exception comment pattern
exception_comment_pattern = re.compile(r"#\s*terraform_authoritative_scanner_ok")

# Function to check for authoritative resources in a file
def check_file_for_authoritative_resources(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()

    authoritative_lines = []
    for line_number, line in enumerate(lines, start=1):
        stripped_line = line.strip()
        # Ignore comment lines
        if stripped_line.startswith("#"):
            continue
        # Check if the line contains any authoritative resource and is not excepted
        if any(resource in line for resource in authoritative_resources):
            if not exception_comment_pattern.search(line):
                authoritative_lines.append((line_number, stripped_line))
    
    return authoritative_lines

# Function to recursively check all Terraform files in a directory
def check_directory_for_authoritative_resources(directory_path, include_dotdirs):
    all_authoritative_lines = []
    for root, dirs, files in os.walk(directory_path):
        if not include_dotdirs:
            # Exclude directories starting with '.'
            dirs[:] = [d for d in dirs if not d.startswith('.')]
        for file in files:
            if file.endswith(".tf"):
                file_path = os.path.join(root, file)
                authoritative_lines = check_file_for_authoritative_resources(file_path)
                if authoritative_lines:
                    all_authoritative_lines.append((file_path, authoritative_lines))
    return all_authoritative_lines

# Main function
def main():
    parser = argparse.ArgumentParser(description="Static analysis of Terraform files for authoritative GCP resources.")
    parser.add_argument("directory", help="Directory path containing Terraform files")
    parser.add_argument("-i", "--include-dotdirs", action="store_true", help="Include directories starting with a dot")
    args = parser.parse_args()

    all_authoritative_lines = check_directory_for_authoritative_resources(args.directory, args.include_dotdirs)
    if all_authoritative_lines:
        for file_path, lines in all_authoritative_lines:
            for line_number, line in lines:
                print(f"Authoritative resource found in {file_path} at line {line_number}: {line}")
        sys.exit(1)
    else:
        print("No authoritative resources found.")
        sys.exit(0)

if __name__ == "__main__":
    main()