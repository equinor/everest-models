import json
from tests import tmpdir, relpath
from spinningjenny.script.fm_well_filter import main_entry_point

TEST_DATA_PATH = relpath("tests", "testdata", "well_filter")


@tmpdir(TEST_DATA_PATH)
def test_drill_plan_filter_entry():
    wells_file = "schedule_wells.json"
    filter_file = "keep_wells_drill_plan.json"
    out_file = "test_wells.json"
    expected_out_file = "correct_out_schedule_filter.json"

    args = ["--input", wells_file, "--keep", filter_file, "--output", out_file]

    main_entry_point(args)

    with open(expected_out_file, "r") as f:
        expected_filter_output = json.load(f)

    with open(out_file, "r") as f:
        filter_output = json.load(f)

    assert expected_filter_output == filter_output


@tmpdir(TEST_DATA_PATH)
def test_well_filter_keep_entry():
    wells_file = "wells.json"
    filter_file = "keep_wells.json"
    out_file = "test_wells.json"
    expected_out_file = "correct_out.json"

    args = ["--input", wells_file, "--keep", filter_file, "--output", out_file]

    main_entry_point(args)

    with open(expected_out_file, "r") as f:
        expected_filter_output = json.load(f)

    with open(out_file, "r") as f:
        filter_output = json.load(f)

    assert expected_filter_output == filter_output


@tmpdir(TEST_DATA_PATH)
def test_well_filter_remove_entry():
    wells_file = "wells.json"
    filter_file = "remove_wells.json"
    out_file = "test_wells.json"
    expected_out_file = "correct_out.json"

    args = ["--input", wells_file, "--remove", filter_file, "--output", out_file]

    main_entry_point(args)

    with open(expected_out_file, "r") as f:
        expected_filter_output = json.load(f)

    with open(out_file, "r") as f:
        filter_output = json.load(f)

    assert expected_filter_output == filter_output
