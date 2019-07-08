import yaml
import json

from datetime import datetime
from os import path

from ecl.summary import EclSum
from configsuite import ConfigSuite
from spinningjenny import customized_logger


try:
    from spinningjenny.version import version

    __version__ = version
except ImportError:
    __version__ = "0.0.0"


DATE_FORMAT = "%Y-%m-%d"


def date2str(date):
    return datetime.strftime(date, DATE_FORMAT)


def str2date(date_str):
    return datetime.strptime(date_str, DATE_FORMAT)


def valid_file(file_path, parser):
    if not path.isfile(file_path):
        parser.error("File not found: {}".format(file_path))
    return file_path


def valid_ecl_file(file_path, parser):
    # We don't check valid_file, as the input may be a basename
    # (e.g. NAME is valid input as long as NAME.UNSMRY and NAME.SMSPEC exists)
    try:
        return EclSum(file_path)
    except (IOError, OSError):
        parser.error("Could not load eclipse summary from file: {}".format(file_path))


def valid_yaml_file(file_path, parser):
    valid_file(file_path, parser)
    try:
        return load_yaml(file_path)
    except (yaml.YAMLError, yaml.MarkedYAMLError) as e:
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
        return str2date(date).date()
    except ValueError:
        parser.error(
            "Not a valid ISO8601 formatted date (YYYY-MM-DD): '{}'.".format(date)
        )


def valid_config(file_path, schema, parser):
    dict_config = valid_yaml_file(file_path, parser)
    config = ConfigSuite(dict_config, schema)
    if not config.valid:
        parser.error(
            "Invalid config file: {}\n{}".format(
                file_path, "\n".join([err.msg for err in config.errors])
            )
        )
    return config


def write_json_to_file(dictionary, file_name):
    with open(file_name, "w") as outfile:
        json.dump(dictionary, outfile, indent=2, separators=(",", ": "))


def write_yaml_to_file(dictionary, file_name):
    with open(file_name, "w") as outfile:
        yaml.safe_dump(dictionary, outfile, default_flow_style=False)


def load_yaml(file_path):
    with open(file_path, "r") as input_file:
        input_data = input_file.readlines()
        try:
            loaded_yaml = yaml.safe_load("".join(input_data))
            return loaded_yaml
        except yaml.YAMLError as exc:
            if hasattr(exc, "problem_mark"):
                mark = exc.problem_mark
                raise yaml.YAMLError(
                    str(exc)
                    + "\nError in line: {}\n {}^)".format(
                        input_data[mark.line], " " * mark.column
                    )
                )
