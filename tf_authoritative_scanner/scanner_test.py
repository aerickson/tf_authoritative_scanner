import pytest
import os
import tempfile
import subprocess

from tf_authoritative_scanner.scanner import TFAuthoritativeScanner


class TestTFAuthoritativeScanner:
    @pytest.fixture
    def scanner(self):
        return TFAuthoritativeScanner(include_dotdirs=False, verbosity=1)

    @pytest.fixture
    def mock_file(self, tmp_path):
        file = tmp_path / "test.tf"
        file.write_text('resource "google_project_iam_binding" "test" {}')
        return file

    @pytest.fixture
    def temp_tf_file(self):
        with tempfile.NamedTemporaryFile(suffix=".tf", delete=False) as temp_file:
            temp_file.write(b"""
            resource "google_project_iam_binding" "binding" {
                project = "my-project"
                role    = "roles/viewer"
                members = [
                    "user:viewer@example.com",
                ]
            }
            """)
            temp_file.close()
            yield temp_file.name
        os.remove(temp_file.name)

    @pytest.fixture
    def temp_tf_dir(self, temp_tf_file):
        temp_dir = tempfile.TemporaryDirectory()
        tf_file_path = os.path.join(temp_dir.name, os.path.basename(temp_tf_file))
        with open(tf_file_path, "w") as f:
            f.write("""
            resource "google_project_iam_binding" "binding" {
                project = "my-project"
                role    = "roles/viewer"
                members = [
                    "user:viewer@example.com",
                ]
            }

            # terraform_authoritative_scanner_ok
            resource "google_project_iam_binding" "binding" {
                project = "my-project"
                role    = "roles/viewer"
                members = [
                    "user:viewer@example.com",
                ]
            }
            """)
        yield temp_dir.name
        temp_dir.cleanup()

    @pytest.fixture
    def temp_tf_file_with_exception_same_line(self):
        with tempfile.NamedTemporaryFile(suffix=".tf", delete=False) as temp_file:
            temp_file.write(b"""
            resource "google_project_iam_binding" "binding" { # terraform_authoritative_scanner_ok
                project = "my-project"
                role    = "roles/viewer"
                members = [
                    "user:viewer@example.com",
                ]
            }
            """)
            temp_file.close()
            yield temp_file.name
        os.remove(temp_file.name)

    @pytest.fixture
    def temp_tf_file_with_exception_previous_line(self):
        with tempfile.NamedTemporaryFile(suffix=".tf", delete=False) as temp_file:
            temp_file.write(b"""
            # terraform_authoritative_scanner_ok
            resource "google_project_iam_binding" "binding" {
                project = "my-project"
                role    = "roles/viewer"
                members = [
                    "user:viewer@example.com",
                ]
            }
            """)
            temp_file.close()
            yield temp_file.name
        os.remove(temp_file.name)

    @pytest.fixture
    def temp_tf_file_authoritative_resource_name_but_not_resource(self):
        with tempfile.NamedTemporaryFile(suffix=".tf", delete=False) as temp_file:
            temp_file.write(b"""
            resource "non_authoritative" "google_deployment_accounts_compute_admin_google_project_iam_binding" {
            project = "fxci-production-level3-workers"
            role    = "roles/compute.admin"
            member  = "serviceAccount:test3333"
            }
            """)
            temp_file.close()
            yield temp_file.name
        os.remove(temp_file.name)

    @pytest.fixture
    def temp_non_authoritative_tf_file(self):
        with tempfile.NamedTemporaryFile(suffix=".tf", delete=False) as temp_file:
            temp_file.write(b"""
            resource "google_compute_instance" "instance" {
                name         = "test-instance"
                machine_type = "n1-standard-1"
                zone         = "us-central1-a"
            }
            """)
            temp_file.close()
            yield temp_file.name
        os.remove(temp_file.name)

    def test_initialization(self, scanner):
        assert not scanner.include_dotdirs
        assert scanner.verbosity == 1

    def test_check_file_for_authoritative_resources(self, scanner, mock_file):
        result = scanner.check_file_for_authoritative_resources(mock_file)
        assert result["authoritative"]

    def test_check_file_for_authoritative_resources_with_exception(self, scanner, tmp_path):
        file = tmp_path / "test_exception.tf"
        file.write_text('# terraform_authoritative_scanner_ok\nresource "google_project_iam_binding" "test" {}')
        result = scanner.check_file_for_authoritative_resources(file)
        assert len(result["excepted_lines"]) == 1

    def test_check_directory_fail(self, scanner, temp_tf_dir):
        r = scanner.check_paths_for_authoritative_resources([temp_tf_dir])
        assert r["files_scanned"] == 1
        assert len(r["results"]) == 1
        assert r["results"][0]["authoritative"]
        assert len(r["results"][0]["authoritative_lines"]) == 1
        assert len(r["results"][0]["excepted_lines"]) == 1

    def test_check_directory_ok(self, scanner, temp_non_authoritative_tf_file):
        r = scanner.check_paths_for_authoritative_resources([temp_non_authoritative_tf_file])
        assert r["files_scanned"] == 1
        assert len(r["results"]) == 1
        assert not r["results"][0]["authoritative"]
        assert len(r["results"][0]["authoritative_lines"]) == 0
        assert len(r["results"][0]["excepted_lines"]) == 0

    def test_check_ar_in_name(self, scanner, temp_tf_file_authoritative_resource_name_but_not_resource):
        r = scanner.check_paths_for_authoritative_resources([temp_tf_file_authoritative_resource_name_but_not_resource])
        assert r["files_scanned"] == 1
        assert len(r["results"][0]["authoritative_lines"]) == 0
        assert len(r["results"][0]["excepted_lines"]) == 0

    def test_check_exclude_comment_inline(self, scanner, temp_tf_file_with_exception_same_line):
        r = scanner.check_paths_for_authoritative_resources([temp_tf_file_with_exception_same_line])
        assert r["files_scanned"] == 1
        assert len(r["results"][0]["authoritative_lines"]) == 0
        assert len(r["results"][0]["excepted_lines"]) == 1

    def test_check_exclude_comment_previous_line(self, scanner, temp_tf_file_with_exception_previous_line):
        r = scanner.check_paths_for_authoritative_resources([temp_tf_file_with_exception_previous_line])
        assert r["files_scanned"] == 1
        assert len(r["results"][0]["authoritative_lines"]) == 0
        assert len(r["results"][0]["excepted_lines"]) == 1

    # main tests

    def test_main_function(self, temp_tf_dir):
        result = subprocess.run(["tfas", temp_tf_dir], capture_output=True, text=True)
        assert "1 of 1 scanned files are authoritative" in result.stdout
        assert result.returncode == 1

    def test_main_function_invalid(self):
        result = subprocess.run(["tfas", "bad_path_xyy888"], capture_output=True, text=True)
        assert result.returncode == 1

    def test_main_directory_fail(self, temp_tf_dir):
        result = subprocess.run(["tfas", temp_tf_dir], capture_output=True, text=True)
        assert result.stderr == ""
        assert "FAIL: 1 of 1 scanned files are authoritative.\n" in result.stdout
        # ensure that authoritative messages are emitted in non-verbose mode
        assert "AUTHORITATIVE" in result.stdout
        assert result.returncode == 1

    def test_main_directory_ok(self, temp_non_authoritative_tf_file):
        result = subprocess.run(["tfas", "-v", temp_non_authoritative_tf_file], capture_output=True, text=True)
        assert result.stderr == ""
        assert "PASS: 0 of 1 scanned files are authoritative.\n" in result.stdout
        assert result.returncode == 0

    def test_main_directory_verbose(self, temp_tf_dir):
        result = subprocess.run(["tfas", "-v", temp_tf_dir], capture_output=True, text=True)
        assert result.stderr == ""
        assert result.returncode == 1

    def test_main_directory_exception(self, temp_tf_file_with_exception_same_line):
        result = subprocess.run(["tfas", "-v", temp_tf_file_with_exception_same_line], capture_output=True, text=True)
        assert result.stderr == ""
        assert result.returncode == 0

    # tests for authoritative_resource_in_line

    def test_authoritative_resource_in_line_basic(self, scanner):
        assert scanner.authoritative_resource_in_line('resource "google_project_iam_binding" "binding" {')
        assert not scanner.authoritative_resource_in_line('resource "google_project_iam_funtime" "binding" {')

    def test_authoritative_resource_in_line_complex(self, scanner):
        # AR in the comment
        assert not scanner.authoritative_resource_in_line(
            'resource "google_project_iam_funtime" "a_google_project_iam_binding_test" {'
        )
        # AR in a string
        assert not scanner.authoritative_resource_in_line('a = "google_project_iam_binding"')

    # tests for build_gcp_resource_doc_url_from_name

    def test_build_gcp_resource_doc_url_from_name(self, scanner):
        assert (
            scanner.build_gcp_resource_doc_url_from_name("google_project_iam_binding")
            == "https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/google_project_iam"
        )

    # test is_gcp_resource_name_authoritative

    def test_is_gcp_resource_name_authoritative(self, scanner):
        assert scanner.is_gcp_resource_name_authoritative("google_project_iam_binding")
        assert scanner.is_gcp_resource_name_authoritative("google_project_iam_audit_config")
