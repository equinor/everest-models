import json

from sub_testdata import INTERPRET_WELL_DRILL as TEST_DATA

from spinningjenny.jobs.fm_interpret_well_drill.tasks import interpret_well_drill


def test_interpret_well_drill(copy_testdata_tmpdir):
    copy_testdata_tmpdir(TEST_DATA)
    out_file = "test_wells.json"
    expected_out_file = "correct_out.json"

    wells_filter = interpret_well_drill("optimizer_values.yml", out_file)

    with open(expected_out_file, "r") as f:
        expected_output = json.load(f)

    assert len(wells_filter) == len(expected_output)
    assert set(wells_filter) == set(expected_output)
