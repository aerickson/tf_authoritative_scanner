import os
import subprocess
import tempfile
import pytest
from pathlib import Path


@pytest.fixture
def temp_terraform_dir():
    # Create a temporary directory
    with tempfile.TemporaryDirectory() as tempdir:
        # Create a .tf file in the directory to simulate a Terraform directory
        tf_file_path = Path(tempdir) / "main.tf"
        tf_file_path.write_text("# comment to just get this moving")

        # Change to the temporary directory
        old_cwd = os.getcwd()
        os.chdir(tempdir)

        yield tempdir

        # Change back to the original directory
        os.chdir(old_cwd)


class TestWrapper:
    def test_is_terraform_directory(self, temp_terraform_dir):
        result = subprocess.run(["tfast", "--version"], capture_output=True, text=True)
        assert "No Terraform files found" not in result.stderr, "The directory should contain .tf files"

    def test_run_tfas_and_terraform(self, temp_terraform_dir):
        result = subprocess.run(["tfast", "plan"], capture_output=True, text=True)

        assert "lharasdf" in result.stdout
        # assert "Successfully ran `tfas .`" in result.stdout, "The script should successfully run `tfas .`"
        # assert "Continuing with `terraform plan`" in result.stdout, "The script should continue with `terraform plan`"
        assert result.returncode == 0, "The script should exit with 0"

    def test_print_ascii_art_banner(self, temp_terraform_dir):
        result = subprocess.run(["tfast", "--version"], capture_output=True, text=True)
        assert result.returncode == 0, "The script should exit with 0"

    def test_no_terraform_files(self):
        with tempfile.TemporaryDirectory() as tempdir:
            old_cwd = os.getcwd()
            os.chdir(tempdir)
            result = subprocess.run(["tfast", "plan"], capture_output=True, text=True)
            os.chdir(old_cwd)
            assert "No Terraform files found" in result.stdout, "The script should exit if no .tf files are found"
            assert result.returncode == 1, "The script should exit with 1"
