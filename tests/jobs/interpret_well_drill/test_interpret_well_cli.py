import json

from utils import relpath, tmpdir

from spinningjenny.jobs.fm_interpret_well_drill.cli import main_entry_point

TEST_DATA_PATH = relpath("tests", "testdata", "interpret_well_drill")


@tmpdir(TEST_DATA_PATH)
def test_interpret_well_drill_entry():
    optimizer_values_file = "optimizer_values.yml"
    out_file = "test.json"
    expected_out_file = "correct_out.json"

    args = ["--input", optimizer_values_file, "--output", out_file]

    main_entry_point(args)

    with open(expected_out_file, "r") as f:
        expected_filter_output = json.load(f)

    with open(out_file, "r") as f:
        filter_output = json.load(f)

    assert len(expected_filter_output) == len(filter_output)
    assert set(expected_filter_output) == set(filter_output)
