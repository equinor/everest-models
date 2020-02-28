from __future__ import absolute_import
import filecmp
from ecl.summary import EclSum

from tests import tmpdir, relpath
from spinningjenny.strip_dates_job import strip_dates, process_dates
from spinningjenny.script.fm_strip_dates import main_entry_point
from spinningjenny import str2date

TEST_DATA_PATH = relpath("tests", "testdata", "stripdates")


def test_format_dates():
    dates = [str2date(date) for date in ["2000-01-01", "2001-02-1", "2003-1-01"]]
    formatted_dates = process_dates(dates)
    expected_dates = [[2000, 1, 1], [2001, 2, 1], [2003, 1, 1]]

    assert formatted_dates == expected_dates


@tmpdir(TEST_DATA_PATH)
def test_strip_dates_reek():
    dates = [[2000, 1, 1], [2001, 2, 1], [2003, 1, 1]]
    # Run the strip dates job
    strip_dates("REEK-0.UNSMRY", dates)

    # Check results
    assert filecmp.cmp("REEK-0.UNSMRY", "REEK-OUT.UNSMRY", shallow=False)


@tmpdir(TEST_DATA_PATH)
def test_strip_dates_egg():
    dates = [
        [2014, 5, 30],
        [2014, 8, 28],
        [2014, 11, 26],
        [2015, 2, 24],
        [2015, 5, 25],
        [2015, 8, 23],
        [2015, 11, 21],
        [2016, 2, 19],
        [2016, 5, 19],
    ]
    # Run the strip dates job
    strip_dates("EGG.UNSMRY", dates)

    # Check results
    assert filecmp.cmp("EGG.UNSMRY", "EGG-OUT.UNSMRY", shallow=False)


@tmpdir(TEST_DATA_PATH)
def test_strip_dates_preserves_last_report_date():
    for file_name in ["REEK-0.UNSMRY", "EGG.UNSMRY"]:
        ecl_sum_in = EclSum(file_name)
        last_report_date = ecl_sum_in.report_dates[-1]

        dates = []
        # Run the strip dates job stripping all report steps
        strip_dates(file_name, dates)

        ecl_sum_result = EclSum(file_name)

        # The stripped summary file should only contain the last report date from
        # the original summary file
        assert len(ecl_sum_result.report_dates) == 1
        assert ecl_sum_result.report_dates[0] == last_report_date
