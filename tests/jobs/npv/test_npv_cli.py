import pytest
from jobs.npv.helper import assert_written_npv

from spinningjenny.jobs.fm_npv import cli

_CONFIG_FILE = "input_data.yml"
_CONFIG_FILE_NO_WELL_COSTS = "input_data_no_well_costs.yml"


def test_npv_entry(tmpdir, copy_npv_testdata_tmpdir, parser_mock):
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
        cli.main_entry_point(args + [f])
        assert_written_npv(tmpdir, expected_npv=691981114.68, out_path="test")


def test_npv_entry_no_input(tmpdir, copy_npv_testdata_tmpdir, parser_mock, capsys):
    args = [
        "--summary",
        "MOCKED.UNSMRY",
        "--config",
        _CONFIG_FILE,
        "--output",
        "test",
    ]
    with pytest.raises(SystemExit) as e:
        cli.main_entry_point(args)
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
    cli.main_entry_point(args)
