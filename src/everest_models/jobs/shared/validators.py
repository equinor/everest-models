import argparse
import datetime
import json
import pathlib
from os import W_OK, access
from typing import Any, Dict, Iterable

import ruamel.yaml as yaml
from pydantic import BaseModel, ValidationError
from resdata.summary import Summary

from everest_models.jobs.shared import io_utils as io


def is_writable_path(value: str) -> pathlib.Path:
    """Validate if given value is a writable filepath.

    Args:
        value (str): filepath to be validated

    Raises:
        argparse.ArgumentTypeError: Is a directory
        argparse.ArgumentTypeError: No access to Directory
        argparse.ArgumentTypeError: No access to File

    Returns:
        pathlib.Path: valid filepath
    """
    path = pathlib.Path(value)
    if not (path.exists() or access(parent := path.parent, W_OK)):
        raise argparse.ArgumentTypeError(f"Can not write to directory: {parent}")

    if path.is_dir():
        raise argparse.ArgumentTypeError(f"Path '{path}' is a directory")

    if path.exists() and not access(path, W_OK):
        raise argparse.ArgumentTypeError(f"Can not write to file: {path}")

    return path


def valid_ecl_summary(file_path: str) -> Summary:
    """Validate eclipse summary file is correct.

    Args:
        file_path (str): Eclipse summary filepath

    Returns:
        Summary: Eclipse summary instance
    """
    try:
        return Summary(file_path)
    except (IOError, OSError):
        argparse.ArgumentTypeError(
            f"Could not load eclipse summary from file: {file_path}"
        )


def validate_eclipse_path(path: pathlib.Path) -> pathlib.Path:
    if path is None:
        raise ValueError("No Eclipse model path given")
    if not path.parent.exists():
        raise ValueError(f"Directory {path.parent} not found")
    if not any(path.parent.glob(f"{path.stem}.*")):
        raise ValueError(f"Model '{path.stem}' not present in directory: {path.parent}")
    return path


def validate_eclipse_path_argparse(path: pathlib.Path) -> pathlib.Path:
    """Validate model filepath is correctly formatted.

    Args:
        path (pathlib.Path): path to eclipse model file path

    Raises:
        argparse.ArgumentTypeError: fail to meet the filepath constraints

    Returns:
        pathlib.Path: validated eclipse model filepath
    """
    try:
        return validate_eclipse_path(pathlib.Path(path))
    except ValueError as e:
        raise argparse.ArgumentTypeError(str(e)) from e


def valid_iso_date(value: str) -> datetime.date:
    """Validate that value is ISO date string.

    Args:
        value (str): date string

    Raises:
        argparse.ArgumentTypeError: not a ISO date string

    Returns:
        datetime.date: Date instance
    """
    try:
        return datetime.date.fromisoformat(value)
    except ValueError as e:
        raise argparse.ArgumentTypeError(
            f"Not a valid ISO8601 formatted date (YYYY-MM-DD): '{value}'."
        ) from e


def valid_schedule_template(value: str) -> str:
    """collect eclipse file content.

    Args:
        value (str): eclipse filepath

    Returns:
        str: eclipse content
    """
    return pathlib.Path(value).read_text(encoding="utf-8")


def _valid_yaml(path: pathlib.Path) -> Any:
    try:
        return io.load_yaml(path)
    except yaml.YAMLError as e:
        raise argparse.ArgumentTypeError(f"Invalid YAML syntax. {e}") from e


def _valid_json(path: pathlib.Path):
    try:
        return io.load_json(path)
    except json.JSONDecodeError as e:
        raise argparse.ArgumentTypeError(
            f"The file: '{path}' is not a valid json file.\n\t<{e}>"
        ) from e


def valid_input_file(value: str) -> Dict[str, Any]:
    """validate YAML/JSON filepath.

    Args:
        value (str): filepath

    Raises:
        argparse.ArgumentTypeError: Directory or not Found
        argparse.ArgumentTypeError: Unsupported file type

    Returns:
        Dict[str, Any]: Dictionary representation of file content
    """
    path = pathlib.Path(value)
    if not path.exists() or path.is_dir():
        raise argparse.ArgumentTypeError(
            f"The path '{path}' is a directory or file not found."
        )
    if (
        get_content := {
            ".yaml": _valid_yaml,
            ".yml": _valid_yaml,
            ".json": _valid_json,
        }.get(path.suffix)
    ) is None:
        raise argparse.ArgumentTypeError(
            f"Input file extension '{path.suffix}' not supported"
        )
    return get_content(path)


def is_gt_zero(value: str, msg: str) -> int:
    """Is string value greater than zero

    Args:
        value (str): numeric string
        msg (str): error message if less

    Raises:
        argparse.ArgumentTypeError: Not a Number
        argparse.ArgumentTypeError: less than zero

    Returns:
        int: integer casted value
    """
    if not value.lstrip("+-").isnumeric():
        raise argparse.ArgumentTypeError(f"Value '{value}' is not a number")
    if (num := int(value)) <= 0:
        raise argparse.ArgumentTypeError(msg)
    return num


def validate_no_extra_fields(*fields, values: Iterable[str]):
    if extra := ", ".join(set(values) - set(fields)):
        raise ValueError(f"Extra field(s) not allowed: {extra}")
    return values


def _prettify_validation_error_message(error: ValidationError) -> str:
    return "\n".join(
        " -> ".join(
            f"index {key + 1}" if isinstance(key, int) else key
            for key in err["loc"]
            if key != "__root__"
        )
        + f":\n\t{err['msg']}"
        for err in error.errors()
    )


def parse_file(value: str, schema: "BaseModel") -> "BaseModel":
    """Parse filepath content by given schema

    Args:
        value (str): filepath
        schema (BaseModel): schema to use for validation and parsing

    Raises:
        argparse.ArgumentTypeError: Failed to adhere to schema specifications

    Returns:
        pydantic.BaseModel: a schema instance
    """
    value = valid_input_file(value)
    try:
        return schema.parse_obj(value)
    except ValidationError as e:
        raise argparse.ArgumentTypeError(
            f"\n{_prettify_validation_error_message(e)}"
        ) from e
