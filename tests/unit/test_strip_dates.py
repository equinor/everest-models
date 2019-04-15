from __future__ import absolute_import
import filecmp
import sys
from tests import tmpdir, relpath
from spinningjenny.strip_dates_job import strip_dates, process_dates
from spinningjenny.script.strip_dates import main_entry_point
from spinningjenny import str2date

TEST_DATA_PATH = relpath('tests', 'testdata', 'stripdates')


def test_format_dates():
    dates = [str2date(date) for date in ['2000-01-01', '2001-02-1', '2003-1-01']]
    formatted_dates = process_dates(dates)
    expected_dates = [[2000, 1, 1], [2001, 2, 1], [2003, 1, 1]]

    assert formatted_dates == expected_dates


@tmpdir(TEST_DATA_PATH)
def test_strip_dates():
    dates = [[2000, 1, 1], [2001, 2, 1], [2003, 1, 1]]
    # Run the strip dates job
    strip_dates("REEK-0.UNSMRY", dates)

    # Check results
    assert filecmp.cmp("REEK-0.UNSMRY", "REEK-OUT.UNSMRY", shallow=False)


@tmpdir(TEST_DATA_PATH)
def test_strip_date_entry_point():
    sys.argv = ['strip_sum',
                '--summary', 'REEK-0.UNSMRY',
                '--dates', '2000-01-01', '2001-02-01', '2003-01-01']

    main_entry_point()
    # Check results
    assert filecmp.cmp("REEK-0.UNSMRY", "REEK-OUT.UNSMRY", shallow=False)
