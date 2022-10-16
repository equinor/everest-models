import json
import os

from utils import relpath, tmpdir

from spinningjenny.jobs.fm_interpret_well_drill.cli import (
    main_entry_point as interpret_entry,
)
from spinningjenny.jobs.fm_well_filter.cli import main_entry_point as well_filter_entry

TEST_DATA_PATH = relpath("tests", "testdata")


@tmpdir(TEST_DATA_PATH)
def test_drill_plan_filter_entry():
    optimizer_values_file = os.path.join("interpret_well_drill", "optimizer_values.yml")
    wells_file = os.path.join("well_filter", "wells.json")
    wells_filter_file = "keep_wells.json"
    out_file = "test.json"
    expected_out_file = os.path.join("well_filter", "correct_out.json")

    args = ["--input", optimizer_values_file, "--output", wells_filter_file]
    interpret_entry(args)

    args = ["--input", wells_file, "--keep", wells_filter_file, "--output", out_file]
    well_filter_entry(args)

    with open(expected_out_file, "r") as f:
        expected_filter_output = json.load(f)

    with open(out_file, "r") as f:
        filter_output = json.load(f)

    assert expected_filter_output == filter_output
