import json

from utils import MockParser, relpath, tmpdir

from jobs.fm_well_filter.tasks import filter_wells, write_results
from jobs.utils.validators import valid_json_file

TEST_DATA_PATH = relpath("tests", "testdata", "well_filter")


@tmpdir(TEST_DATA_PATH)
def test_drill_plan_filter():
    parser = MockParser()
    out_file = "test_wells.json"
    expected_out_file = "correct_out_schedule_filter.json"
    filtered_wells = filter_wells(
        wells=valid_json_file("schedule_wells.json", parser),
        parser=parser,
        keep_wells=valid_json_file("keep_wells_drill_plan.json", parser),
    )
    write_results(filtered_wells, out_file)

    with open(expected_out_file, "r") as f:
        expected_output = json.load(f)

    assert filtered_wells == expected_output


@tmpdir(TEST_DATA_PATH)
def test_well_filter_keep():
    parser = MockParser()
    out_file = "test_wells.json"
    expected_out_file = "correct_out.json"
    filtered_wells = filter_wells(
        wells=valid_json_file("wells.json", parser),
        parser=parser,
        keep_wells=valid_json_file("keep_wells.json", parser),
    )
    write_results(filtered_wells, out_file)

    with open(expected_out_file, "r") as f:
        expected_output = json.load(f)

    assert filtered_wells == expected_output


@tmpdir(TEST_DATA_PATH)
def test_well_filter_remove():
    parser = MockParser()
    out_file = "test_wells.json"
    expected_out_file = "correct_out.json"
    filtered_wells = filter_wells(
        wells=valid_json_file("wells.json", parser),
        parser=parser,
        remove_wells=valid_json_file("remove_wells.json", parser),
    )
    write_results(filtered_wells, out_file)

    with open(expected_out_file, "r") as f:
        expected_output = json.load(f)

    assert filtered_wells == expected_output


@tmpdir(TEST_DATA_PATH)
def test_well_filter_both():
    parser = MockParser()
    filter_wells(
        wells=valid_json_file("wells.json", parser),
        parser=parser,
        remove_wells=valid_json_file("remove_wells.json", parser),
        keep_wells=valid_json_file("keep_wells.json", parser),
    )

    assert (
        "well_filter requires either the --keep or --remove flag to be set, not both"
        in parser.get_error()
    )


@tmpdir(TEST_DATA_PATH)
def test_well_filter_neither():
    parser = MockParser()
    filter_wells(
        wells=valid_json_file("wells.json", parser),
        parser=parser,
        remove_wells=None,
        keep_wells=None,
    )

    assert (
        "well_filter requires either the --keep or --remove flag to be set"
        in parser.get_error()
    )
