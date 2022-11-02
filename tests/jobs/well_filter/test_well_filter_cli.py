import json

from sub_testdata import WELL_FILTER as TEST_DATA

from spinningjenny.jobs.fm_well_filter.cli import main_entry_point


def test_drill_plan_filter_entry(copy_testdata_tmpdir):
    copy_testdata_tmpdir(TEST_DATA)
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


def test_well_filter_keep_entry(copy_testdata_tmpdir):
    copy_testdata_tmpdir(TEST_DATA)
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


def test_well_filter_remove_entry(copy_testdata_tmpdir):
    copy_testdata_tmpdir(TEST_DATA)
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
