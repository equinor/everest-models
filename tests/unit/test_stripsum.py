from __future__ import absolute_import
import unittest
import filecmp
from tests import tmpdir, relpath
from forwardmodels.scripts.strip_sum import strip_sum

TEST_DATA_PATH = relpath('tests', 'testdata', 'stripsum')


class StripSumTest(unittest.TestCase):

    @tmpdir(TEST_DATA_PATH )
    def test_strip_sum(self):
        # Run the stripsum job
        strip_sum("REEK-0.UNSMRY",  "dates")

        # Check results
        self.assertTrue(
            filecmp.cmp("REEK-0.UNSMRY", "REEK-OUT.UNSMRY", shallow=False)
        )


if __name__ == "__main__":
    unittest.main()
