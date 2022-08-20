from spinningjenny import load_yaml
from spinningjenny.script.fm_drill_date_planner import main_entry_point
from tests import relpath, tmpdir

TEST_DATA_PATH = relpath("tests", "testdata", "drill_date_planner")


@tmpdir(TEST_DATA_PATH)
def test_drill_date_planner_main_entry_point():
    arguments = (
        "--input wells.json -opt controls.json --bounds 0.0 1.0"
        " --max-days 300 -o output.json"
    ).split()

    main_entry_point(arguments)

    test_output = load_yaml("output.json")
    expected_output = load_yaml("expected_result.json")

    assert test_output == expected_output
