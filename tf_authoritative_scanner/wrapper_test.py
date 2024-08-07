import os
import subprocess
import tempfile
import pytest


@pytest.fixture
def temp_tf_file():
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
def temp_tf_dir_empty():
    temp_dir = tempfile.TemporaryDirectory()
    yield temp_dir.name
    temp_dir.cleanup()


@pytest.fixture
def temp_tf_dir_good(temp_tf_file):
    temp_dir = tempfile.TemporaryDirectory()
    tf_file_path = os.path.join(temp_dir.name, os.path.basename(temp_tf_file))
    with open(tf_file_path, "w") as f:
        f.write("""
        # harmless file

        """)
    yield temp_dir.name
    temp_dir.cleanup()


@pytest.fixture
def temp_tf_dir_bad(temp_tf_file):
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


class TestWrapper:
    def test_is_terraform_directory(self):
        result = subprocess.run(["tfast", "--version"], capture_output=True, text=True)
        assert result.returncode == 0

    def test_run_tfas_and_terraform_help(self, temp_tf_dir_bad: str):
        result = subprocess.run(["tfast", "--help"], cwd=temp_tf_dir_bad, capture_output=True, text=True)
        assert "Ensures Terraform code in the current directory" in result.stdout
        assert result.returncode == 0

    def test_run_tfas_and_terraform_bad(self, temp_tf_dir_bad: str):
        result = subprocess.run(["tfast", "plan"], cwd=temp_tf_dir_bad, capture_output=True, text=True)
        assert "Not running `terraform" in result.stdout
        assert result.returncode == 1

    # ideally this wouldn't require `terraform` to be installed (nice that Github Actions has it)
    #   - injecting a different command fails, because the execve call effectively kills pytest
    #   - TODO: try mocking the terraform command
    def test_run_tfas_and_terraform_good(self, temp_tf_dir_good: str):
        result = subprocess.run(["tfast", "-A", "plan"], cwd=temp_tf_dir_good, capture_output=True, text=True)
        assert "Terraform has compared your real infrastructure against your configuration" in result.stdout
        assert "found no differences" in result.stdout
        assert result.returncode == 0

    def test_run_tfas_and_terraform_empty(self, temp_tf_dir_empty: str):
        result = subprocess.run(["tfast", "-A", "plan"], cwd=temp_tf_dir_empty, capture_output=True, text=True)
        assert (
            "No Terraform files found in the current directory. Please ensure you're in a directory with .tf files."
            in result.stdout
        )
        assert result.returncode == 1
