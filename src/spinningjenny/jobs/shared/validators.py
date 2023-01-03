import argparse
import datetime
import json
import pathlib
from os import W_OK, access, path

import ruamel.yaml as yaml
from ecl.summary import EclSum
from pydantic import BaseModel, ValidationError

from spinningjenny.jobs.shared.io_utils import load_yaml


def valid_file(file_path, parser):
    if not path.isfile(file_path):
        parser.error("File not found: {}".format(file_path))
    return file_path


def is_writable(file_path, parser):
    if path.exists(file_path):
        if path.isfile(file_path):
            if not access(file_path, W_OK):
                parser.error("Can not write to file: {}".format(file_path))
        else:
            parser.error("Path '{}' is a directory".format(file_path))

    # If file does not exist, verify that parent directory is writable
    pdir = path.dirname(file_path) or "."
    if not access(pdir, W_OK):
        parser.error("Can not write to directory: {}".format(pdir))

    return file_path


def is_writable_path(value: str) -> pathlib.Path:
    path = pathlib.Path(value)
    if not (path.exists() or access(pdir := path.parent, W_OK)):
        raise argparse.ArgumentTypeError(f"Can not write to directory: {pdir}")

    if path.is_dir():
        raise argparse.ArgumentTypeError(f"Path '{path}' is a directory")

    if path.exists() and not access(path, W_OK):
        raise argparse.ArgumentTypeError(f"Can not write to file: {path}")

    return path


def valid_json_file(file_path, parser):
    valid_file(file_path, parser)
    try:
        with open(file_path, "r") as f:
            json_dict = json.load(f)
        return json_dict
    except json.JSONDecodeError as e:
        parser.error("File <{}> is not a valid json file: {}".format(file_path, str(e)))


def valid_ecl_file(file_path, parser):
    # We don't check valid_file, as the input may be a basename
    # (e.g. NAME is valid input as long as NAME.UNSMRY and NAME.SMSPEC exists)
    try:
        return EclSum(file_path)
    except (IOError, OSError):
        parser.error("Could not load eclipse summary from file: {}".format(file_path))


def valid_ecl_summary(file_path: str) -> EclSum:
    try:
        return EclSum(file_path)
    except (IOError, OSError):
        argparse.ArgumentTypeError(
            f"Could not load eclipse summary from file: {file_path}"
        )


def valid_yaml_file(file_path, parser):
    valid_file(file_path, parser)
    try:
        return load_yaml(file_path)
    except yaml.YAMLError as e:
        parser.error(
            "The config file: <{}> contains invalid YAML syntax: {}".format(
                file_path, str(e)
            )
        )
    except Exception as e:
        parser.error(
            "Loading yaml config <{}> failed with unexpected exception: {}".format(
                file_path, str(e)
            )
        )


def valid_date(date, parser):
    try:
        return datetime.date.fromisoformat(date)
    except ValueError:
        parser.error(
            "Not a valid ISO8601 formatted date (YYYY-MM-DD): '{}'.".format(date)
        )


def valid_iso_date(value):
    try:
        return datetime.date.fromisoformat(value)
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"Not a valid ISO8601 formatted date (YYYY-MM-DD): '{value}'."
        )


def valid_input_file(value: str):
    path = pathlib.Path(value)
    if not path.exists() or path.is_dir():
        raise argparse.ArgumentTypeError(
            f"The path '{path}' is a directory or file not found."
        )
    if path.suffix in (".yaml", ".yml"):
        try:
            return yaml.YAML(typ="safe", pure=True).load(path.read_bytes())
        except yaml.YAMLError as e:
            raise argparse.ArgumentTypeError(
                f"The file: '{path}' contains invalid YAML syntax.\n\t<{e}>"
            )
    if path.suffix == ".json":
        with path.open("r", encoding="utf-8") as fp:
            try:
                return json.load(fp)
            except json.JSONDecodeError as e:
                raise argparse.ArgumentTypeError(
                    f"The file: '{path}' is not a valid json file.\n\t<{e}>"
                )
    raise argparse.ArgumentTypeError(
        f"Input file extension '{path.suffix}' not supported"
    )


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
        raise argparse.ArgumentTypeError(f"\n{_prettify_validation_error_message(e)}")
