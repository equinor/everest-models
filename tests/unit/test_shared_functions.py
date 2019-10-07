import os
import stat

from tests import tmpdir, MockParser
from spinningjenny import is_writable


@tmpdir(path=None)
def test_is_writable_valid():
    mock_parser = MockParser()

    _ = is_writable("non_existing_valid_filename", mock_parser)
    assert mock_parser.get_error() is None

    with open("existing_file", "a") as _:
        pass

    _ = is_writable("existing_file", mock_parser)
    assert mock_parser.get_error() is None

    os.mkdir("existing_dir")

    _ = is_writable("existing_dir/valid_filename", mock_parser)
    assert mock_parser.get_error() is None

    with open("existing_dir/existing_file", "a") as _:
        pass

    _ = is_writable("existing_dir/existing_file", mock_parser)
    assert mock_parser.get_error() is None


@tmpdir(path=None)
def test_is_writable_non_existing_dir():
    mock_parser = MockParser()

    _ = is_writable("non_existing_dir/valid_filename", mock_parser)
    assert "Can not write to directory" in mock_parser.get_error()


@tmpdir(path=None)
def test_is_writable_write_to_dir():
    mock_parser = MockParser()
    os.mkdir("existing_dir")

    _ = is_writable("existing_dir", mock_parser)
    assert "Path 'existing_dir' is a directory" in mock_parser.get_error()


@tmpdir(path=None)
def test_is_writable_no_write_permissions():
    mock_parser = MockParser()

    os.mkdir("existing_dir")
    os.chmod("existing_dir", stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)

    _ = is_writable("existing_dir/valid_filename", mock_parser)
    assert "Can not write to directory" in mock_parser.get_error()
