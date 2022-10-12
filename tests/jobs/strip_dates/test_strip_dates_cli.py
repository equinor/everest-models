import filecmp
import logging

import pytest
from jobs.strip_dates import MODULE

from jobs.fm_strip_dates.cli import main_entry_point


@pytest.mark.sub_dir(MODULE)
def test_strip_date_entry_point(copy_testdata_tmpdir):
    args = [
        "--summary",
        "EGG.UNSMRY",
        "--dates",
        "2014-05-30",
        "2014-08-28",
        "2014-11-26",
        "2015-02-24",
        "2015-05-25",
        "2015-08-23",
        "2015-11-21",
        "2016-02-19",
        "2016-05-19",
    ]

    main_entry_point(args)
    # Check results
    assert filecmp.cmp("EGG.UNSMRY", "EGG-OUT.UNSMRY", shallow=False)


@pytest.mark.sub_dir(MODULE)
def test_strip_date_entry_point_missing_dates_error(caplog, copy_testdata_tmpdir):
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


@pytest.mark.sub_dir(MODULE)
def test_strip_date_entry_point_missing_dates_warn(caplog, copy_testdata_tmpdir):
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
