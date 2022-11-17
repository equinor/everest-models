import argparse
import datetime
import os
import pathlib
import stat

import pytest
from hypothesis import given
from hypothesis import strategies as st
from pydantic import BaseModel, FilePath
from sub_testdata import VALIDATORS as TEST_DATA
from utils import MockParser

from spinningjenny.jobs.shared.validators import (
    is_gt_zero,
    is_writable,
    is_writable_path,
    parse_file,
    valid_input_file,
    valid_iso_date,
    valid_json_file,
)


def test_is_writable_valid(copy_testdata_tmpdir):
    copy_testdata_tmpdir()
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


def test_is_writable_non_existing_dir(copy_testdata_tmpdir):
    copy_testdata_tmpdir()
    mock_parser = MockParser()

    _ = is_writable("non_existing_dir/valid_filename", mock_parser)
    assert "Can not write to directory" in mock_parser.get_error()


def test_is_writable_write_to_dir(copy_testdata_tmpdir):
    copy_testdata_tmpdir()
    mock_parser = MockParser()
    os.mkdir("existing_dir")

    _ = is_writable("existing_dir", mock_parser)
    assert "Path 'existing_dir' is a directory" in mock_parser.get_error()


def test_is_writable_no_write_permissions(copy_testdata_tmpdir):
    copy_testdata_tmpdir()
    mock_parser = MockParser()

    os.mkdir("existing_dir")
    os.chmod("existing_dir", stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)

    _ = is_writable("existing_dir/valid_filename", mock_parser)
    assert "Can not write to directory" in mock_parser.get_error()


def test_valid_json_file(copy_testdata_tmpdir):
    copy_testdata_tmpdir(TEST_DATA)
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


def write_file(path, txt):
    def func():
        with open(path, "w") as fp:
            fp.write(txt)

    return func


@pytest.mark.parametrize(
    "path, func, match",
    [
        pytest.param(
            "empty.json",
            pathlib.Path("empty.json").touch,
            "The file: 'empty.json' is not a valid json file.\n\t",
            id="empty json",
        ),
        pytest.param(
            ".", None, "The path '.' is a directory or file not found.", id="directory"
        ),
        pytest.param(
            "not_exist",
            None,
            "The path 'not_exist' is a directory or file not found.",
            id="file not exist",
        ),
        pytest.param(
            "empty.ou",
            pathlib.Path("empty.ou").touch,
            "Input file extension '.ou' not supported",
            id="unsupported extension",
        ),
        pytest.param(
            "bad.json",
            write_file("bad.json", "{"),
            "The file: 'bad.json' is not a valid json file.\n\t",
            id="bad json",
        ),
        pytest.param(
            "bad.yaml",
            write_file("bad.yaml", "{"),
            "The file: 'bad.yaml' contains invalid YAML syntax.\n\t",
            id="bad yaml",
        ),
        pytest.param(
            "bad.yml",
            write_file("bad.yml", "{"),
            "The file: 'bad.yml' contains invalid YAML syntax.\n\t",
            id="bad yml",
        ),
    ],
)
def test_valid_input_file_error(path, func, match, switch_cwd_tmp_path):
    if func is not None:
        func()
    with pytest.raises(argparse.ArgumentTypeError, match=match) as e:
        valid_input_file(path)


class TestModel(BaseModel):
    class Config:
        frozen = True
        extra = "forbid"


class TestModelB(TestModel):
    test_field_1: float


class TestModelA(TestModel):
    test_field_a: FilePath
    test_field_b: TestModelB


def test_parse_file_error(switch_cwd_tmp_path):
    write_file(
        "test.json",
        '{"test_field_x": "s", "test_field_a": ".", "test_field_b": {"test_field_1": "r"}}',
    )()
    print(pathlib.Path("test.json").read_text())
    with pytest.raises(argparse.ArgumentTypeError) as e:
        parse_file("test.json", TestModelA)

    assert (
        str(e.value)
        == """
test_field_a:
\tpath "." does not point to a file
test_field_b -> test_field_1:
\tvalue is not a valid float
test_field_x:
\textra fields not permitted"""
    )


@given(st.integers(max_value=0))
def test_is_gt_zero_error(value):
    with pytest.raises(argparse.ArgumentTypeError, match="max-days must be > 0"):
        is_gt_zero(str(value), "max-days must be > 0")


@given(st.integers(min_value=1))
def test_is_gt_zero(value):
    assert value == is_gt_zero(str(value), "not important")


@given(st.characters(blacklist_categories=("Nd", "Nl", "No")))
def test_is_gt_zero_not_a_number(value):
    with pytest.raises(argparse.ArgumentTypeError) as e:
        is_gt_zero(value, "not important")
    assert f"Value '{value}' is not a number" == str(e.value)


@pytest.mark.parametrize(
    "path, func, match",
    [
        pytest.param(".", None, "Path '.' is a directory", id="directory"),
        # need to create a better test to pass on MacOS
        # pytest.param(
        #     "/usr/lib/openssh/ssh-keysign",
        #     None,
        #     "Can not write to file: /usr/lib/openssh/ssh-keysign",
        #     id="no file permission",
        # ),
    ],
)
def test_is_writable_path_error(path, func, match, switch_cwd_tmp_path):
    path = func() if func is not None else path

    with pytest.raises(argparse.ArgumentTypeError, match=match):
        is_writable_path(path)


@given(st.dates())
def test_valid_iso_date(value):
    assert value == valid_iso_date(str(value))


@pytest.mark.parametrize(
    "format",
    (
        "%d-%m-%y",
        "%d-%m-%Y",
        "%-d-%m-%y",
        "%d-%b-%y",
        "%d-%B-%y",
        "%d-%-m-%y",
        "%Y/%m/%d",
    ),
)
def test_not_valid_iso_date(format):
    date = datetime.datetime.now().strftime(format)
    with pytest.raises(
        argparse.ArgumentTypeError,
        match=r"Not a valid ISO8601 formatted date \(YYYY-MM-DD\): " f"'{date}'.",
    ):
        valid_iso_date(date)


@given(st.text())
def test_not_valid_date(value):
    with pytest.raises(argparse.ArgumentTypeError) as e:
        valid_iso_date(value)
    assert f"Not a valid ISO8601 formatted date (YYYY-MM-DD): '{value}'." in str(
        e.value
    )
