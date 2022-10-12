import os

import pytest

from spinningjenny.script import fm_npv
from tests.unit.test_npv import assert_written_npv, options

_CONFIG_FILE = "input_data.yml"
_CONFIG_FILE_NO_WELL_COSTS = "input_data_no_well_costs.yml"
_TEST_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "../tests/testdata/npv/"
)


def test_npv_entry(tmpdir, options):
    input_files = ["wells.json", "wells_completion_dates.json", "wells_mix_dates.json"]
    args = [
        "--summary",
        "MOCKED.UNSMRY",
        "--config",
        _CONFIG_FILE,
        "--output",
        "test",
        "--input",
    ]
    for f in input_files:
        fm_npv.main_entry_point(args + [f])
        assert_written_npv(tmpdir, expected_npv=691981114.68, out_path="test")


def test_npv_entry_no_input(tmpdir, options, capsys):
    args = [
        "--summary",
        "MOCKED.UNSMRY",
        "--config",
        _CONFIG_FILE,
        "--output",
        "test",
    ]
    with pytest.raises(SystemExit) as e:
        fm_npv.main_entry_point(args)
    assert e.value.code == 2
    _, err = capsys.readouterr()
    assert "Well costs specified, but the -i/--input flag is missing" in err

    # No exception when there are not costs in the config file:
    args = [
        "--summary",
        "MOCKED.UNSMRY",
        "--config",
        _CONFIG_FILE_NO_WELL_COSTS,
        "--output",
        "test",
    ]
    fm_npv.main_entry_point(args)
