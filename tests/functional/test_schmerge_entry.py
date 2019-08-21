from spinningjenny.script.fm_schmerge import main_entry_point
from tests import tmpdir, relpath

TEST_DATA_PATH = relpath("tests", "testdata", "schmerge")


@tmpdir(TEST_DATA_PATH)
def test_schmerge_main_entry_point():
    filename_expected_result = "expected_result.tmpl"
    filename_input_schedule = "original_schedule.tmpl"
    filename_injection_list = "schedule_input.json"
    filename_output = "out.tmpl"

    args = [
        "--input",
        filename_input_schedule,
        "--config",
        filename_injection_list,
        "--output",
        filename_output,
    ]

    main_entry_point(args)

    with open(filename_expected_result, "r") as f:
        expected_schedule_string = f.read()

    with open(filename_output, "r") as f:
        schmerge_output = f.read()

    assert expected_schedule_string == schmerge_output
