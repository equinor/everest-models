from __future__ import absolute_import
import filecmp
from tests import tmpdir, relpath
from spinningjenny.strip_sum_job import strip_sum

TEST_DATA_PATH = relpath('tests', 'testdata', 'stripsum')


@tmpdir(TEST_DATA_PATH)
def test_strip_sum():

    # Run the stripsum job
    strip_sum("REEK-0.UNSMRY",  "dates")

    # Check results
    assert filecmp.cmp("REEK-0.UNSMRY", "REEK-OUT.UNSMRY", shallow=False)



