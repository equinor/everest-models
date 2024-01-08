import argparse
import datetime
import pathlib

import pytest
from everest_models.jobs.shared.validators import (
    _prettify_validation_error_message,
    is_gt_zero,
    is_writable_path,
    parse_file,
    valid_input_file,
    valid_iso_date,
)
from hypothesis import given
from hypothesis import strategies as st
from pydantic import BaseModel, FilePath


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
            r"\sInvalid file syntax:\s.*empty.json\s",
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
            r"Unsupported file encoding:\s\s.*empty.ou",
            id="unsupported extension",
        ),
        pytest.param(
            "bad.json",
            write_file("bad.json", "{"),
            r"\sInvalid file syntax:\s.*bad.json\s",
            id="bad json",
        ),
        pytest.param(
            "bad.yaml",
            write_file("bad.yaml", "{"),
            r"\sInvalid file syntax:\s.*bad.yaml\s",
            id="bad yaml",
        ),
        pytest.param(
            "bad.yml",
            write_file("bad.yml", "{"),
            r"\sInvalid file syntax:\s.*bad.yml\s",
            id="bad yml",
        ),
    ],
)
def test_valid_input_file_error(path, func, match, switch_cwd_tmp_path):
    if func is not None:
        func()
    with pytest.raises(argparse.ArgumentTypeError, match=match):
        valid_input_file(path)


class Model(BaseModel):
    class Config:
        frozen = True
        extra = "forbid"


class ModelB(Model):
    test_field_1: float


class ModelA(Model):
    test_field_a: FilePath
    test_field_b: ModelB


def test_parse_file_error(switch_cwd_tmp_path):
    write_file(
        "test.json",
        '{"test_field_x": "s", "test_field_a": ".", "test_field_b": {"test_field_1": "r"}}',
    )()
    print(pathlib.Path("test.json").read_text())
    with pytest.raises(argparse.ArgumentTypeError) as e:
        parse_file("test.json", ModelA)

    assert (
        str(e.value)
        == """
test_field_a:
\tPath does not point to a file
test_field_b -> test_field_1:
\tInput should be a valid number, unable to parse string as a number
test_field_x:
\tExtra inputs are not permitted"""
    )


@given(st.integers(max_value=0))
def test_is_gt_zero_error(value):
    with pytest.raises(argparse.ArgumentTypeError, match="max-days must be > 0"):
        is_gt_zero(str(value), "max-days must be > 0")


@given(st.integers(min_value=1))
def test_is_gt_zero(value):
    assert value == is_gt_zero(str(value), "not important")


@given(st.characters(whitelist_categories=("Lu", "Ll", "Lm")))
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


def test_prettify_validation_error_message(monkeypatch):
    class ValidationError:
        def errors(self):
            return [
                {"loc": ("__root__", 5, "name"), "msg": "not a name"},
                {"loc": ("__root__", "field_a", "child"), "msg": "baby"},
                {"loc": ("field_b", 4, "sub", "child"), "msg": "nested"},
            ]

    assert (
        _prettify_validation_error_message(ValidationError())
        == """index 6 -> name:
\tnot a name
field_a -> child:
\tbaby
field_b -> index 5 -> sub -> child:
\tnested"""
    )
