from spinningjenny.script.fm_drill_planner import main_entry_point
from spinningjenny import load_yaml
from tests import tmpdir, relpath

TEST_DATA_PATH = relpath("tests", "testdata", "drill_planner")


@tmpdir(TEST_DATA_PATH)
def test_main_entry_point_partial_wells():
    arguments = [
        "--input",
        "partial_wells.json",
        "--config",
        "config.yml",
        "--optimizer",
        "optimizer_values.yml",
        "--output",
        "partial_out.json",
    ]

    main_entry_point(arguments)

    test_output = load_yaml("partial_out.json")
    expected_output = load_yaml("partial_correct_out.json")

    assert test_output == expected_output
