import os
import stat

from utils import MockParser, relpath, tmpdir

from jobs.utils.validators import is_writable, valid_json_file

VALIDATOR_PATH = relpath("tests", "testdata", "validators")


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


@tmpdir(path=VALIDATOR_PATH)
def test_valid_json_file():
    valid_json_path = "valid_json.json"
    invalid_json_path = "invalid_json.json"

    mock_parser = MockParser()
    valid_json_file(valid_json_path, mock_parser)
    assert mock_parser.get_error() is None

    mock_parser = MockParser()
    valid_json_file(invalid_json_path, mock_parser)

    # py2 and py3 have slightly different error messages
    error_msgs = (
        "File <invalid_json.json> is not a valid json file: "
        "Expecting ',' delimiter: line 6 column 5 (char 55)"
    )
    assert error_msgs in mock_parser.get_error()
