from spinningjenny import str2date
from spinningjenny.schmerge_job import (
    merge_schedule,
    _extract_comments,
    _insert_extracted_comments,
    _add_dates_to_schedule,
    _get_dates_from_schedule,
)
from spinningjenny.script.fm_schmerge import main_entry_point
from tests import tmpdir, relpath

TEST_DATA_PATH = relpath("tests", "testdata", "schmerge")


@tmpdir(TEST_DATA_PATH)
def test__add_dates_to_schedule():
    filename_input_schedule = "original_schedule.tmpl"
    filename_expected_inserted_dates = "inserted_dates.tmpl"
    with open(filename_input_schedule, "r") as f:
        schedule_string = f.read()

    with open(filename_expected_inserted_dates, "r") as f:
        expected_inserted_dates = f.read()

    date_strings_to_add = ["2000-01-01", "2016-08-16", "2021-04-24"]
    dates_to_add = [str2date(date_string) for date_string in date_strings_to_add]
    schedule_string, placeholder_dict = _extract_comments(schedule_string)
    schedule_inserted_dates = _add_dates_to_schedule(schedule_string, dates_to_add)
    schedule_inserted_dates = _insert_extracted_comments(
        schedule_inserted_dates, placeholder_dict
    )
    assert schedule_inserted_dates == expected_inserted_dates


@tmpdir(TEST_DATA_PATH)
def test_add_dates_to_schedule_without_initial_dates():
    # Test dates can be added to schedule file that doesn't contain initial date
    date_strings_to_add = ["2000-01-01", "2021-08-16", "2015-04-24"]
    dates_to_add = [str2date(date_string) for date_string in date_strings_to_add]

    with open("no_dates_schedule.tmpl", "r") as f:
        schedule_string = f.read()

    schedule_string, placeholder_dict = _extract_comments(schedule_string)
    new_schedule_string = _add_dates_to_schedule(schedule_string, dates_to_add)
    new_schedule_string = _insert_extracted_comments(
        new_schedule_string, placeholder_dict
    )
    dates_in_schedule = _get_dates_from_schedule(new_schedule_string)

    assert sorted(dates_to_add) == dates_in_schedule


@tmpdir(TEST_DATA_PATH)
def test__extract_comments():
    filename_input_schedule = "original_schedule.tmpl"
    filename_placeholder = "placeholder_schedule.tmpl"
    with open(filename_input_schedule, "r") as f:
        schedule_string = f.read()

    with open(filename_placeholder, "r") as f:
        schedule_placeholder_string = f.read()

    placeholder_output, placeholder_dict = _extract_comments(schedule_string)

    assert placeholder_output == schedule_placeholder_string

    inserted_output = _insert_extracted_comments(placeholder_output, placeholder_dict)

    assert inserted_output == schedule_string


@tmpdir(TEST_DATA_PATH)
def test_schmerge():
    filename_expected_result = "expected_result.tmpl"
    filename_input_schedule = "original_schedule.tmpl"
    filename_injection_list = "schedule_input.json"
    filename_output = "out.tmpl"

    schedule_string = merge_schedule(
        schedule_file=filename_input_schedule,
        inject_file=filename_injection_list,
        output_file=filename_output,
    )

    with open(filename_expected_result, "r") as f:
        expected_schedule_string = f.read()

    with open(filename_output, "r") as f:
        schmerge_output = f.read()

    assert schedule_string == expected_schedule_string
    assert schmerge_output == schedule_string
    # Check if result and expected result are equal


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
