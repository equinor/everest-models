import json

from sub_testdata import WELL_FILTER as TEST_DATA
from utils import MockParser

from spinningjenny.jobs.fm_well_filter.tasks import filter_wells, write_results
from spinningjenny.jobs.utils.validators import valid_json_file


def test_drill_plan_filter(copy_testdata_tmpdir):
    copy_testdata_tmpdir(TEST_DATA)
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


def test_well_filter_keep(copy_testdata_tmpdir):
    copy_testdata_tmpdir(TEST_DATA)
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


def test_well_filter_remove(copy_testdata_tmpdir):
    copy_testdata_tmpdir(TEST_DATA)
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


def test_well_filter_both(copy_testdata_tmpdir):
    copy_testdata_tmpdir(TEST_DATA)
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


def test_well_filter_neither(copy_testdata_tmpdir):
    copy_testdata_tmpdir(TEST_DATA)
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
