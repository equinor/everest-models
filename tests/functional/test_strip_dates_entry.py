from __future__ import absolute_import
import filecmp
import logging
import pytest

from tests import tmpdir, relpath
from spinningjenny.script.fm_strip_dates import main_entry_point

TEST_DATA_PATH = relpath("tests", "testdata", "stripdates")


@tmpdir(TEST_DATA_PATH)
def test_strip_date_entry_point():
    args = [
        "--summary",
        "EGG.UNSMRY",
        "--dates",
        "2014-5-30",
        "2014-8-28",
        "2014-11-26",
        "2015-2-24",
        "2015-5-25",
        "2015-8-23",
        "2015-11-21",
        "2016-2-19",
        "2016-5-19",
    ]

    main_entry_point(args)
    # Check results
    assert filecmp.cmp("EGG.UNSMRY", "EGG-OUT.UNSMRY", shallow=False)


@tmpdir(TEST_DATA_PATH)
def test_strip_date_entry_point_missing_dates_error(caplog):
    args = [
        "--summary",
        "EGG.UNSMRY",
        "--dates",
        "1900-01-01",
    ]

    with pytest.raises(SystemExit), caplog.at_level(logging.ERROR):
        main_entry_point(args)
    # Check log
    assert "ERROR" in caplog.text and "Missing date" in caplog.text


@tmpdir(TEST_DATA_PATH)
def test_strip_date_entry_point_missing_dates_warn(caplog):
    args = [
        "--summary",
        "EGG.UNSMRY",
        "--dates",
        "1900-01-01",
        "--allow-missing-dates",
    ]

    with caplog.at_level(logging.WARNING):
        main_entry_point(args)
    # Check log
    assert "WARNING" in caplog.text and "Missing date" in caplog.text
