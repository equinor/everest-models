import argparse
import datetime
import pathlib
from json import JSONDecodeError
from os import W_OK, access
from typing import Any, Iterable, Type, TypeVar

from pydantic import BaseModel, ValidationError
from resdata.summary import Summary
from ruamel.yaml.error import YAMLError

from everest_models.jobs.shared.io_utils import load_supported_file_encoding

T = TypeVar("T", bound=BaseModel)


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
    except (IOError, OSError) as e:
        raise argparse.ArgumentTypeError(
            f"Could not load eclipse summary from file: {file_path}"
        ) from e


def validate_eclipse_path(path: pathlib.Path) -> pathlib.Path:
    if path is None:
        raise ValueError("No Eclipse model path given")
    if not path.parent.exists():
        raise ValueError(f"Directory {path.parent} not found")
    if not any(path.parent.glob(f"{path.stem}.*")):
        raise ValueError(f"Model '{path.stem}' not present in directory: {path.parent}")
    return path


def validate_eclipse_path_argparse(path: str) -> pathlib.Path:
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


def valid_input_file(value: str) -> Any:
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
    try:
        return load_supported_file_encoding(path)
    except (JSONDecodeError, YAMLError) as e:
        raise argparse.ArgumentTypeError(
            f"\nInvalid file syntax:\n{path.absolute()}\n{e}"
        ) from e
    except ValueError as ve:
        raise argparse.ArgumentTypeError(str(ve)) from ve


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
            if key != "root"
        )
        + f":\n\t{err['msg']}"
        for err in error.errors()
    )


def parse_file(value: str, schema: Type[T]) -> T:
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
        return schema.model_validate(value)
    except ValidationError as e:
        raise argparse.ArgumentTypeError(
            f"\n{_prettify_validation_error_message(e)}"
        ) from e
