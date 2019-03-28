from __future__ import absolute_import
import unittest
import subprocess
import os
import filecmp
from tests import tmpdir, relpath

TEST_DATA_PATH = relpath('tests', 'testdata', 'stripsum')


class StripSumTest(unittest.TestCase):

    @tmpdir(TEST_DATA_PATH )
    def test_run(self):
        cmd = relpath('workflows', 'scripts', 'stripsum.py')
        self.assertTrue(os.access(cmd, os.X_OK))

        # Run the stripsum job
        cmd_list = [cmd, "REEK-0.UNSMRY",  "dates"]
        subprocess.check_call(cmd_list)

        # Check results
        self.assertTrue(
            filecmp.cmp("REEK-0.UNSMRY", "REEK-OUT.UNSMRY", shallow=False)
        )


if __name__ == "__main__":
    unittest.main()
