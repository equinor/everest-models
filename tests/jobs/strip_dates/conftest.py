import pytest


@pytest.fixture(scope="module")
def strip_dates_base_args():
    return (
        "--summary",
        "EGG.UNSMRY",
        "--dates",
    )


@pytest.fixture(scope="module")
def string_dates():
    return (
        "2014-05-30",
        "2014-08-28",
        "2014-11-26",
        "2015-02-24",
        "2015-05-25",
        "2015-08-23",
        "2015-11-21",
        "2016-02-19",
        "2016-05-19",
    )
