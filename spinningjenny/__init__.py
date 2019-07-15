from datetime import datetime
from spinningjenny import customized_logger
from os import path

from ecl.summary import EclSum

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
