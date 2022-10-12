import json

from utils import relpath, tmpdir

from jobs.fm_interpret_well_drill.tasks import interpret_well_drill

TEST_DATA_PATH = relpath("tests", "testdata", "interpret_well_drill")


@tmpdir(TEST_DATA_PATH)
def test_interpret_well_drill():
    dakota_values_file = "optimizer_values.yml"
    out_file = "test_wells.json"
    expected_out_file = "correct_out.json"

    wells_filter = interpret_well_drill(dakota_values_file, out_file)

    with open(expected_out_file, "r") as f:
        expected_output = json.load(f)

    assert len(wells_filter) == len(expected_output)
    assert set(wells_filter) == set(expected_output)
