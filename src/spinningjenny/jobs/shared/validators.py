import argparse
import datetime
import json
import pathlib
from os import W_OK, access

import ruamel.yaml as yaml
from ecl.summary import EclSum
from pydantic import BaseModel, ValidationError


def is_writable_path(value: str) -> pathlib.Path:
    path = pathlib.Path(value)
    if not (path.exists() or access(parent := path.parent, W_OK)):
        raise argparse.ArgumentTypeError(f"Can not write to directory: {parent}")

    if path.is_dir():
        raise argparse.ArgumentTypeError(f"Path '{path}' is a directory")

    if path.exists() and not access(path, W_OK):
        raise argparse.ArgumentTypeError(f"Can not write to file: {path}")

    return path


def valid_ecl_summary(file_path: str) -> EclSum:
    try:
        return EclSum(file_path)
    except (IOError, OSError):
        argparse.ArgumentTypeError(
            f"Could not load eclipse summary from file: {file_path}"
        )


def valid_iso_date(value):
    try:
        return datetime.date.fromisoformat(value)
    except ValueError as e:
        raise argparse.ArgumentTypeError(
            f"Not a valid ISO8601 formatted date (YYYY-MM-DD): '{value}'."
        ) from e


def valid_schedule_template(value: str):
    return pathlib.Path(value).read_text(encoding="utf-8")


def _valid_yaml(path: pathlib.Path):
    try:
        return yaml.YAML(typ="safe", pure=True).load(path.read_bytes())
    except yaml.YAMLError as e:
        raise argparse.ArgumentTypeError(
            f"The file: '{path}' contains invalid YAML syntax.\n\t<{e}>"
        ) from e


def _valid_json(path: pathlib.Path):
    with path.open("r", encoding="utf-8") as fp:
        try:
            return json.load(fp)
        except json.JSONDecodeError as e:
            raise argparse.ArgumentTypeError(
                f"The file: '{path}' is not a valid json file.\n\t<{e}>"
            ) from e


def valid_input_file(value: str):
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
    if not value.lstrip("+-").isnumeric():
        raise argparse.ArgumentTypeError(f"Value '{value}' is not a number")
    if (num := int(value)) <= 0:
        raise argparse.ArgumentTypeError(msg)
    return num


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


def parse_file(value: str, schema: "BaseModel"):
    value = valid_input_file(value)
    try:
        return schema.parse_obj(value)
    except ValidationError as e:
        raise argparse.ArgumentTypeError(
            f"\n{_prettify_validation_error_message(e)}"
        ) from e
