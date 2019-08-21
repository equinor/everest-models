import json
from tests import tmpdir, relpath
from spinningjenny.interpret_well_drill_job import interpret_well_drill
from spinningjenny.script.fm_interpret_well_drill import main_entry_point

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
