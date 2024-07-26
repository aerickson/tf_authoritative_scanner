import os
import pytest
import tempfile
import subprocess
from tf_authoritative_scanner.scanner import TFAuthoritativeScanner


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
def temp_tf_dir(temp_tf_file):
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
        """)
    yield temp_dir.name
    temp_dir.cleanup()


@pytest.fixture
def temp_tf_file_with_exception_same_line():
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
def temp_tf_file_with_exception_previous_line():
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
def temp_non_authoritative_tf_file():
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


def test_check_file_for_authoritative_resources(temp_tf_file):
    scanner = TFAuthoritativeScanner(temp_tf_file, include_dotdirs=False)
    authoritative_lines = scanner.check_file_for_authoritative_resources(temp_tf_file)
    assert len(authoritative_lines) > 0


# def test_check_directory_for_authoritative_resources(temp_tf_dir):
#     scanner = TFAuthoritativeScanner(temp_tf_dir, include_dotdirs=False)
#     all_authoritative_lines, total_files = (
#         scanner.check_directory_for_authoritative_resources()
#     )
#     assert total_files == 1
#     assert len(all_authoritative_lines) > 0


def test_check_directory_for_authoritative_resources(temp_tf_dir):
    scanner = TFAuthoritativeScanner(temp_tf_dir, include_dotdirs=False)
    all_authoritative_lines, total_files, _ = (
        scanner.check_directory_for_authoritative_resources()
    )
    assert total_files == 1
    assert len(all_authoritative_lines) > 0


def test_directory_not_exists():
    with pytest.raises(SystemExit):
        scanner = TFAuthoritativeScanner(
            "non_existent_directory", include_dotdirs=False
        )
        scanner.run()


def test_run_verbosity(temp_tf_dir, capsys):
    scanner = TFAuthoritativeScanner(temp_tf_dir, include_dotdirs=False, verbosity=1)
    with pytest.raises(SystemExit):
        scanner.run()
    captured = capsys.readouterr()
    assert "AUTHORITATIVE" in captured.out


def test_run_non_verbosity(temp_tf_dir, capsys):
    scanner = TFAuthoritativeScanner(temp_tf_dir, include_dotdirs=False, verbosity=0)
    with pytest.raises(SystemExit):
        scanner.run()
    captured = capsys.readouterr()
    assert "1 of 1 scanned files are authoritative" in captured.out


def test_run_verbose_level_2(temp_non_authoritative_tf_file, capsys):
    temp_dir = tempfile.TemporaryDirectory()
    temp_file_path = os.path.join(
        temp_dir.name, os.path.basename(temp_non_authoritative_tf_file)
    )
    with open(temp_file_path, "w") as f:
        f.write("""
        resource "google_compute_instance" "instance" {
            name         = "test-instance"
            machine_type = "n1-standard-1"
            zone         = "us-central1-a"
        }
        """)

    scanner = TFAuthoritativeScanner(temp_dir.name, include_dotdirs=False, verbosity=2)
    with pytest.raises(SystemExit):
        scanner.run()
    captured = capsys.readouterr()
    assert "non-authoritative: " in captured.out


def test_exception_comment_same_line(temp_tf_file_with_exception_same_line):
    scanner = TFAuthoritativeScanner(
        temp_tf_file_with_exception_same_line, include_dotdirs=False
    )
    authoritative_lines = scanner.check_file_for_authoritative_resources(
        temp_tf_file_with_exception_same_line
    )
    assert len(authoritative_lines) == 0


def test_exception_comment_previous_line(temp_tf_file_with_exception_previous_line):
    scanner = TFAuthoritativeScanner(
        temp_tf_file_with_exception_previous_line, include_dotdirs=False
    )
    authoritative_lines = scanner.check_file_for_authoritative_resources(
        temp_tf_file_with_exception_previous_line
    )
    assert len(authoritative_lines) == 0


def test_main_function(temp_tf_dir):
    result = subprocess.run(["tfas", temp_tf_dir], capture_output=True, text=True)
    assert "1 of 1 scanned files are authoritative" in result.stdout
    assert result.returncode == 1


def test_main_function_invalid():
    result = subprocess.run(["tfas", "bad_path_xyy888"], capture_output=True, text=True)
    # assert "1 of 1 scanned files are authoritative" in result.stdout
    assert result.returncode == 1
