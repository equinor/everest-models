from datetime import datetime

DATE_FORMAT = '%Y-%m-%d'


def date2str(date):
    return datetime.strftime(date, DATE_FORMAT)


def str2date(date_str):
    return datetime.strptime(date_str, DATE_FORMAT)
