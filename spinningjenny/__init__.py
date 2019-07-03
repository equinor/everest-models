from datetime import datetime
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
