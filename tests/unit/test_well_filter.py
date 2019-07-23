import os
import json
import pytest
from tests import tmpdir, relpath
from spinningjenny.well_filter_job import filter_wells
from spinningjenny.script.well_filter import main_entry_point

TEST_DATA_PATH = relpath("tests", "testdata", "well_filter")


@tmpdir(TEST_DATA_PATH)
def test_drill_plan_filter():
    wells_file = "schedule_wells.json"
    filter_file = "keep_wells_drill_plan.json"
    out_file = "test_wells.json"
    expected_out_file = "correct_out_schedule_filter.json"

    filtered_wells = filter_wells(wells_file, out_file, keep_file=filter_file)

    with open(expected_out_file, "r") as f:
        expected_output = json.load(f)

    assert filtered_wells == expected_output


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
def test_well_filter_keep():
    wells_file = "wells.json"
    filter_file = "keep_wells.json"
    out_file = "test_wells.json"
    expected_out_file = "correct_out.json"

    filtered_wells = filter_wells(wells_file, out_file, keep_file=filter_file)

    with open(expected_out_file, "r") as f:
        expected_output = json.load(f)

    assert filtered_wells == expected_output


@tmpdir(TEST_DATA_PATH)
def test_well_filter_remove():
    wells_file = "wells.json"
    filter_file = "remove_wells.json"
    out_file = "test_wells.json"
    expected_out_file = "correct_out.json"

    filtered_wells = filter_wells(wells_file, out_file, remove_file=filter_file)

    with open(expected_out_file, "r") as f:
        expected_output = json.load(f)

    assert filtered_wells == expected_output


@tmpdir(TEST_DATA_PATH)
def test_well_filter_both():
    wells_file = "wells.json"
    filter_file = "keep_remove_wells.json"
    out_file = "test_wells.json"

    # check that ValueError is raised
    with pytest.raises(ValueError):
        _ = filter_wells(
            wells_file, out_file, keep_file=filter_file, remove_file=filter_file
        )


@tmpdir(TEST_DATA_PATH)
def test_well_filter_neither():
    wells_file = "wells.json"
    out_file = "test_wells.json"

    # check that ValueError is raised
    with pytest.raises(ValueError):
        _ = filter_wells(wells_file, out_file, keep_file=None, remove_file=None)


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
