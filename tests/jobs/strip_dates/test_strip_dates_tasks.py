import datetime
import filecmp

import pytest
from ecl.summary import EclSum
from sub_testdata import STRIP_DATES as TEST_DATA

from spinningjenny.jobs.fm_strip_dates.tasks import strip_dates

SUMMARY_CASE = "EGG.UNSMRY"


@pytest.fixture(scope="module")
def strip_dates_summary(path_test_data):
    return EclSum(str(path_test_data / TEST_DATA / SUMMARY_CASE))


def test_strip_dates_egg(string_dates, strip_dates_summary, copy_testdata_tmpdir):
    copy_testdata_tmpdir(TEST_DATA)
    dates = [datetime.date.fromisoformat(date) for date in string_dates]
    # Run the strip dates job
    strip_dates(strip_dates_summary.dates, dates, "EGG.UNSMRY")

    # Check results
    assert filecmp.cmp(SUMMARY_CASE, "EGG-OUT.UNSMRY", shallow=False)


def test_strip_dates_preserves_last_report_date(
    strip_dates_summary, copy_testdata_tmpdir
):
    copy_testdata_tmpdir(TEST_DATA)

    # Run the strip dates job stripping all report steps
    strip_dates(strip_dates_summary.dates, dates=[], summary_path=SUMMARY_CASE)

    ecl_sum_result = EclSum(SUMMARY_CASE)

    # The stripped summary file should only contain the last report date
    # from the original summary file
    assert len(ecl_sum_result.report_dates) == 1
    assert ecl_sum_result.report_dates[0] == strip_dates_summary.report_dates[-1]
