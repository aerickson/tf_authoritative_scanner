#!/usr/bin/env python3

import os
import re
import sys
import argparse
import os.path

from tf_authoritative_scanner.util import _get_version


class TFAuthoritativeScanner:
    # hand-verified authoritative GCP resources that don't match the _binding or _policy suffixes
    # TODO: figure out a way of extracting these from the provider's source code or docs
    #   - https://github.com/GoogleCloudPlatform/magic-modules/
    #       cd mmv1/third_party/terraform/website/docs/r
    #       rg -i authoritat | grep -vi 'non-authoritative'
    additional_authoritative_gcp_resources = [
        "google_project_iam_audit_config",  # https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/google_project_iam
        "google_storage_bucket_acl",  # https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/storage_bucket_acl
        "google_dns_record_set",  # https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/dns_record_set
    ]

    exception_comment_pattern = re.compile(r"#\s*terraform_authoritative_scanner_ok")

    def __init__(self, include_dotdirs, verbosity=0):
        self.include_dotdirs = include_dotdirs
        self.verbosity = verbosity

    # examples:
    #   "google_project_iam_audit_config",  # https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/google_project_iam
    #   "google_folder_iam_binding",  # https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/google_folder_iam
    def build_gcp_resource_doc_url_from_name(self, resource_name):
        # remove _binding and _policy from resource_name
        # TODO: handle non _binding or _policy ARs
        resource_name = resource_name.replace("_binding", "")
        resource_name = resource_name.replace("_policy", "")
        # remove google_ prefix
        resource_name = resource_name.replace("google_", "")
        return f"https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/google_{resource_name}"

    # from inspecting the GCP provider, basically anything with the '_policy' or '_binding'
    #   in the resource name is authoritative aka 'google*policy' or 'google*binding'.
    # - see the GCP provider's docs
    #   https://github.com/GoogleCloudPlatform/magic-modules/blob/19bec78daccb664b42f915e1fc552dea6a64ea93/mmv1/templates/terraform/resource_iam.html.markdown.tmpl#L59-L60
    def is_gcp_resource_name_authoritative(self, resource_name):
        # if resource is on hardcoded list
        if resource_name in self.additional_authoritative_gcp_resources:
            return {"authoritative": True, "confidence": 100}
        # if the resource name starts with 'google_' and ends with '_binding' or '_policy' then it is authoritative
        if resource_name.startswith("google_") and (
            resource_name.endswith("_binding") or resource_name.endswith("_policy")
        ):
            return {"authoritative": True, "confidence": 85}
        if resource_name.startswith("google_") and (resource_name.endswith("_audit_config")):
            return {"authoritative": True, "confidence": 80}
        return {"authoritative": False, "confidence": 90}

    # improvements over earlier substring-based approach:
    #   - check word parts vs substring
    #   - use patterns vs hardcoded list
    def authoritative_resource_in_line(self, line):
        _confidence = 100
        word_parts = _get_first_two_word_parts(line)
        first_word, second_word = word_parts
        if first_word == "resource":
            r = self.is_gcp_resource_name_authoritative(second_word)
            authoritative = r["authoritative"]
            _confidence = r["confidence"]
            if authoritative:
                return {"authoritative": True, "confidence": _confidence}
        return {"authoritative": False, "confidence": _confidence}

    def check_file_for_authoritative_resources(self, file_path):
        with open(file_path, "r") as file:
            lines = file.readlines()

        authoritative_lines = []
        excepted_lines = []
        file_authoritative = False
        previous_line = ""
        for line_number, line in enumerate(lines, start=1):
            stripped_line = line.strip()
            # Ignore comment lines
            if stripped_line.startswith("#"):
                previous_line = stripped_line
                continue
            # Check if the line contains any authoritative resource and is not excepted
            r = self.authoritative_resource_in_line(stripped_line)
            r_authoritative = r["authoritative"]
            _r_confidence = r["confidence"]
            if r_authoritative:
                if not self.exception_comment_pattern.search(line) and not self.exception_comment_pattern.search(
                    previous_line
                ):
                    authoritative_lines.append({"line_number": line_number, "line": stripped_line})
                    file_authoritative = True
                else:
                    excepted_lines.append({"line_number": line_number, "line": stripped_line})
            previous_line = stripped_line

        return {
            "file_path": file_path,
            "authoritative": file_authoritative,
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


# TODO: move these to util files


def _verify_paths(paths):
    for path in paths:
        if not os.path.exists(path):
            print(f"Error: The path '{path}' does not exist.")
            sys.exit(1)


def _remove_inner_quotes(s):
    # Define patterns for both single and double quotes
    double_quote_pattern = r"\"([^\"]*?)\""
    single_quote_pattern = r"\'([^\']*?)\'"

    # Remove inner quotes for double quotes
    s = re.sub(double_quote_pattern, lambda m: m.group(0).replace('"', ""), s)
    # Remove inner quotes for single quotes
    s = re.sub(single_quote_pattern, lambda m: m.group(0).replace("'", ""), s)

    return s


# known issue: returns "", "" on less than two word-part strings
def _get_first_two_word_parts(string):
    word_parts = string.split()
    if len(word_parts) < 2:
        return "", ""
    first_word = _remove_inner_quotes(word_parts[0])
    second_word = _remove_inner_quotes(word_parts[1])
    return first_word, second_word


# TODO: move this to a cli.py file
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
        version=_get_version("__init__.py"),
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
