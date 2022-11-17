from sub_testdata import DRILL_DATE_PLANNER as TEST_DATA

from spinningjenny.jobs.fm_drill_date_planner.cli import main_entry_point
from spinningjenny.jobs.shared.io_utils import load_yaml


def test_drill_date_planner_main_entry_point(copy_testdata_tmpdir):
    copy_testdata_tmpdir(TEST_DATA)

    arguments = (
        "--input wells.json -opt controls.json --bounds 0.0 1.0"
        " --max-days 300 -o output.json"
    ).split()

    main_entry_point(arguments)

    test_output = load_yaml("output.json")
    expected_output = load_yaml("expected_result.json")

    assert test_output == expected_output
