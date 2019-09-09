import os

from spinningjenny.script import fm_npv
from tests.unit.test_npv import assert_written_npv, options

_SUMMARY_FILE = "REEK-0.UNSMRY"
_CONFIG_FILE = "input_data.yml"
_TEST_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "../tests/testdata/npv/"
)


def test_main_entry_point(tmpdir, options):

    args = [
        "--summary",
        _SUMMARY_FILE,
        "--config",
        _CONFIG_FILE,
        "--output",
        "test",
        "--input",
        "wells.json",
    ]

    fm_npv.main_entry_point(args)
    assert_written_npv(tmpdir, expected_npv=939374969.82, out_path="test")
