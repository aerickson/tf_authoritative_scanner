import tf_authoritative_scanner.util as util

import tempfile
import os
import pytest


class TestUtil:
    @pytest.fixture
    def temp_dir_with_version_file(self):
        temp_dir = tempfile.TemporaryDirectory()
        version_file_path = os.path.join(temp_dir.name, "__init__.py")
        with open(version_file_path, "w") as f:
            f.write("__version__ = '4.3.9999'")
        yield temp_dir.name
        temp_dir.cleanup()

    @pytest.fixture
    def temp_empty_dir(self):
        temp_dir = tempfile.TemporaryDirectory()
        yield temp_dir.name
        temp_dir.cleanup()

    def test_remove_leading_trailing_newline(self):
        assert util.remove_leading_trailing_newline("") == ""
        assert util.remove_leading_trailing_newline("a") == "a"
        assert util.remove_leading_trailing_newline("a\n") == "a"
        assert util.remove_leading_trailing_newline("\na") == "a"
        assert util.remove_leading_trailing_newline("a\nb") == "a\nb"

    def test_get_version(self, temp_dir_with_version_file):
        assert util.get_version(f"{temp_dir_with_version_file}/__init__.py") == "4.3.9999"

    def test_get_version_empty_dir(self, temp_empty_dir):
        # should raise an exception FileNotFoundError
        with pytest.raises(FileNotFoundError):
            util.get_version(f"{temp_empty_dir}/__init__.py")
