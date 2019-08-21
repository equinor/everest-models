from __future__ import absolute_import
import filecmp

from tests import tmpdir, relpath
from spinningjenny.script.fm_strip_dates import main_entry_point

TEST_DATA_PATH = relpath("tests", "testdata", "stripdates")


@tmpdir(TEST_DATA_PATH)
def test_strip_date_entry_point():
    args = [
        "--summary",
        "REEK-0.UNSMRY",
        "--dates",
        "2000-01-01",
        "2001-02-01",
        "2003-01-01",
    ]

    main_entry_point(args)
    # Check results
    assert filecmp.cmp("REEK-0.UNSMRY", "REEK-OUT.UNSMRY", shallow=False)
