import os
import pytest
import tempfile
import shutil
from check_authoritative_resources import TFAuthoritativeScanner

class TestTFAuthoritativeScanner:
    def setup_method(self):
        # Create a temporary directory
        self.test_dir = tempfile.mkdtemp()

    def teardown_method(self):
        # Remove the temporary directory
        shutil.rmtree(self.test_dir)

    def create_file(self, filename, content):
        file_path = os.path.join(self.test_dir, filename)
        with open(file_path, 'w') as f:
            f.write(content)
        return file_path

    def test_no_authoritative_resources(self):
        # Create a .tf file with no authoritative resources
        self.create_file('main.tf', """
        resource "google_storage_bucket" "bucket" {
          name     = "my-bucket"
        }
        """)
        
        scanner = TFAuthoritativeScanner(self.test_dir, include_dotdirs=False)
        result = scanner.check_directory_for_authoritative_resources()
        assert len(result) == 0

    def test_authoritative_resources_found(self):
        # Create a .tf file with an authoritative resource
        self.create_file('main.tf', """
        resource "google_project_iam_binding" "binding" {
          project = "my-project"
          role    = "roles/viewer"
          members = ["user:example@example.com"]
        }
        """)
        
        scanner = TFAuthoritativeScanner(self.test_dir, include_dotdirs=False)
        result = scanner.check_directory_for_authoritative_resources()
        assert len(result) == 1

    def test_authoritative_resources_with_exception(self):
        # Create a .tf file with an authoritative resource and an exception comment
        self.create_file('main.tf', """
        resource "google_project_iam_binding" "binding" { # terraform_authoritative_scanner_ok
          project = "my-project"
          role    = "roles/viewer"
          members = ["user:example@example.com"]
        }
        """)
        
        scanner = TFAuthoritativeScanner(self.test_dir, include_dotdirs=False)
        result = scanner.check_directory_for_authoritative_resources()
        assert len(result) == 0

    def test_include_dotdirs(self):
        # Create a .tf file inside a dot directory
        dot_dir = os.path.join(self.test_dir, '.dotdir')
        os.makedirs(dot_dir)
        self.create_file(os.path.join(dot_dir, 'main.tf'), """
        resource "google_project_iam_binding" "binding" {
          project = "my-project"
          role    = "roles/viewer"
          members = ["user:example@example.com"]
        }
        """)
        
        scanner = TFAuthoritativeScanner(self.test_dir, include_dotdirs=True)
        result = scanner.check_directory_for_authoritative_resources()
        assert len(result) == 1

    def test_exclude_dotdirs(self):
        # Create a .tf file inside a dot directory
        dot_dir = os.path.join(self.test_dir, '.dotdir')
        os.makedirs(dot_dir)
        self.create_file(os.path.join(dot_dir, 'main.tf'), """
        resource "google_project_iam_binding" "binding" {
          project = "my-project"
          role    = "roles/viewer"
          members = ["user:example@example.com"]
        }
        """)
        
        scanner = TFAuthoritativeScanner(self.test_dir, include_dotdirs=False)
        result = scanner.check_directory_for_authoritative_resources()
        assert len(result) == 0

    def test_run_no_authoritative_resources(self, capsys):
        # Create a .tf file with no authoritative resources
        self.create_file('main.tf', """
        resource "google_storage_bucket" "bucket" {
          name     = "my-bucket"
        }
        """)
        
        scanner = TFAuthoritativeScanner(self.test_dir, include_dotdirs=False)
        with pytest.raises(SystemExit) as e:
            scanner.run()
        captured = capsys.readouterr()
        assert e.value.code == 0
        assert "No authoritative resources found." in captured.out

    def test_run_authoritative_resources_found(self, capsys):
        # Create a .tf file with an authoritative resource
        self.create_file('main.tf', """
        resource "google_project_iam_binding" "binding" {
          project = "my-project"
          role    = "roles/viewer"
          members = ["user:example@example.com"]
        }
        """)
        
        scanner = TFAuthoritativeScanner(self.test_dir, include_dotdirs=False)
        with pytest.raises(SystemExit) as e:
            scanner.run()
        captured = capsys.readouterr()
        assert e.value.code == 1
        assert "Authoritative resource found" in captured.out

if __name__ == "__main__":
    pytest.main()
