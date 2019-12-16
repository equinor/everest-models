from spinningjenny.script.fm_schmerge import main_entry_point, valid_schmerge_config
from tests import tmpdir, relpath, MockParser

TEST_DATA_PATH = relpath("tests", "testdata", "schmerge")


@tmpdir(TEST_DATA_PATH)
def test_schmerge_main_entry_point():
    filename_expected_result = "expected_result.tmpl"
    filename_schedule = "original_schedule.tmpl"
    filename_injection_list = "schedule_input.json"
    filename_output = "out.tmpl"

    args = [
        "--input",
        filename_injection_list,
        "--schedule",
        filename_schedule,
        "--output",
        filename_output,
    ]

    main_entry_point(args)

    with open(filename_expected_result, "r") as f:
        expected_schedule_string = f.read()

    with open(filename_output, "r") as f:
        schmerge_output = f.read()

    assert expected_schedule_string == schmerge_output


@tmpdir(TEST_DATA_PATH)
def test_valid_schmerge_config():
    invalid_injections = "schedule_input_invalid.json"
    valid_injections = "schedule_input.json"

    mock_parser = MockParser()
    valid_schmerge_config(invalid_injections, mock_parser)
    assert (
        "Json file <schedule_input_invalid.json> misses a required keyword: 'template'"
        in mock_parser.get_error()
    )

    mock_parser = MockParser()
    valid_schmerge_config(valid_injections, mock_parser)
    assert mock_parser.get_error() is None
