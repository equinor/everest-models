import filecmp
import logging

import pytest
from ecl.summary import EclSum
from sub_testdata import STRIP_DATES as TEST_DATA

from everest_models.jobs.fm_strip_dates.cli import main_entry_point


def test_strip_date_entry_point(
    copy_testdata_tmpdir, string_dates, strip_dates_base_args
):
    copy_testdata_tmpdir(TEST_DATA)

    main_entry_point([*strip_dates_base_args, *string_dates])
    # Check results
    assert filecmp.cmp("EGG.UNSMRY", "EGG-OUT.UNSMRY", shallow=False)


def test_strip_date_entry_point_missing_dates_error(
    strip_dates_base_args, copy_testdata_tmpdir, capsys
):
    copy_testdata_tmpdir(TEST_DATA)

    with pytest.raises(SystemExit) as e:
        main_entry_point(
            [
                *strip_dates_base_args,
                "1900-01-01",
            ]
        )

    assert e.value.code == 2
    _, err = capsys.readouterr()
    assert "Missing date(s) in eclipse file EGG.UNSMRY:\n\t1900-01-01" in err


def test_strip_date_entry_point_missing_dates_warn(
    strip_dates_base_args, caplog, copy_testdata_tmpdir
):
    copy_testdata_tmpdir(TEST_DATA)

    with caplog.at_level(logging.WARNING):
        main_entry_point(
            [
                *strip_dates_base_args,
                "2014-05-30",
                "1900-01-01",
                "--allow-missing-dates",
            ]
        )
    # Check log
    assert (
        "WARNING" in caplog.text
        and "Missing date(s) in eclipse file EGG.UNSMRY:\n\t1900-01-01" in caplog.text
    )


def test_strip_date_entry_point_preserves_last_date(
    strip_dates_base_args, copy_testdata_tmpdir
):
    copy_testdata_tmpdir(TEST_DATA)

    main_entry_point(strip_dates_base_args[:-1])

    ecl_sum_result = EclSum("EGG.UNSMRY")

    # The stripped summary file should only contain the last report date
    # from the original summary file
    assert len(ecl_sum_result.report_dates) == 1
    assert str(ecl_sum_result.report_dates[0]) == "2016-05-19"


def test_strip_dates_entry_lint(strip_dates_base_args, copy_testdata_tmpdir):
    copy_testdata_tmpdir(TEST_DATA)

    with pytest.raises(SystemExit) as e:
        main_entry_point([*strip_dates_base_args, "2014-05-30", "--lint"])

    assert e.value.code == 0
