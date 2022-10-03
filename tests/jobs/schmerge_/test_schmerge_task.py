import datetime

import pytest
from jobs.schmerge_ import MODULE
from utils import MockParser

from jobs.fm_schmerge.cli import valid_schmerge_config
from jobs.fm_schmerge.tasks import (
    _add_dates_to_schedule,
    _extract_comments,
    _find_date_index,
    _get_dates_from_schedule,
    _insert_extracted_comments,
    merge_schedule,
)


def test__get_dates_from_schedule():
    schedule_string = """
DATES
 01 'JAN' 2000 /


/

DATES


 2  JAN  2000    12:03:06.1232 /
/

DATES

 28   'JLY' 2015     /

   /

DATES
1 JAN 2020 /
/

DATES
 1 FEB 2020/
/
"""
    dates = _get_dates_from_schedule(schedule_string)
    assert len(dates) == 5
    assert dates[0] == datetime.datetime(2000, 1, 1)
    assert dates[1] == datetime.datetime(2000, 1, 2, 12, 3, 6)
    assert dates[2] == datetime.datetime(2015, 7, 28)
    assert dates[3] == datetime.datetime(2020, 1, 1)
    assert dates[4] == datetime.datetime(2020, 2, 1)


def test__find_date_index():
    schedule_string = """
DATES


 1 JAN 2000 /

/

DATES
 01 JAN 2001 /
--<<2>>
/
"""
    existing_date = datetime.datetime(2000, 1, 1)
    index = _find_date_index(schedule_string, existing_date)
    assert index == 1

    existing_date = datetime.datetime(2001, 1, 1)
    index = _find_date_index(schedule_string, existing_date)
    assert index == 27


def test__add_single_date_to_schedule():
    schedule_string = """
DATES
 01 JAN 2000 /
/

DATES
 01 JAN 2001 /
/
"""
    non_existing_date = datetime.datetime(2005, 1, 1)
    updated_schedule_string = _add_dates_to_schedule(
        schedule_string, [non_existing_date]
    )
    expected_string = """
DATES
 01 JAN 2000 /
/

DATES
 01 JAN 2001 /
/

DATES
 01 JAN 2005 / --ADDED
/

"""
    assert updated_schedule_string == expected_string


@pytest.mark.sub_dir(MODULE)
def test__add_dates_to_schedule(copy_testdata_tmpdir):
    filename_input_schedule = "original_schedule.tmpl"
    filename_expected_inserted_dates = "inserted_dates.tmpl"
    with open(filename_input_schedule, "r") as f:
        schedule_string = f.read()

    with open(filename_expected_inserted_dates, "r") as f:
        expected_inserted_dates = f.read()

    date_strings_to_add = ["2000-01-01", "2016-08-16", "2021-04-24"]
    dates_to_add = [
        datetime.datetime.fromisoformat(date_string)
        for date_string in date_strings_to_add
    ]
    schedule_string, placeholder_dict = _extract_comments(schedule_string)
    schedule_inserted_dates = _add_dates_to_schedule(schedule_string, dates_to_add)
    schedule_inserted_dates = _insert_extracted_comments(
        schedule_inserted_dates, placeholder_dict
    )
    assert schedule_inserted_dates == expected_inserted_dates


@pytest.mark.sub_dir(MODULE)
def test_add_dates_to_schedule_without_initial_dates(copy_testdata_tmpdir):
    # Test dates can be added to schedule file that doesn't contain initial date
    date_strings_to_add = ["2000-01-01", "2021-08-16", "2015-04-24"]
    dates_to_add = [
        datetime.datetime.fromisoformat(date_string)
        for date_string in date_strings_to_add
    ]

    with open("no_dates_schedule.tmpl", "r") as f:
        schedule_string = f.read()

    schedule_string, placeholder_dict = _extract_comments(schedule_string)
    new_schedule_string = _add_dates_to_schedule(schedule_string, dates_to_add)
    new_schedule_string = _insert_extracted_comments(
        new_schedule_string, placeholder_dict
    )
    dates_in_schedule = _get_dates_from_schedule(new_schedule_string)

    assert sorted(dates_to_add) == dates_in_schedule


@pytest.mark.sub_dir(MODULE)
def test__extract_comments(copy_testdata_tmpdir):
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


@pytest.mark.sub_dir(MODULE)
def test_schmerge(copy_testdata_tmpdir):
    filename_expected_result = "expected_result.tmpl"
    filename_input_schedule = "original_schedule.tmpl"
    filename_injection_list = "schedule_input.json"
    filename_output = "out.tmpl"

    mock_parser = MockParser()

    schedule_string = merge_schedule(
        schedule_file=filename_input_schedule,
        injections=valid_schmerge_config(filename_injection_list, mock_parser),
        output_file=filename_output,
    )

    with open(filename_expected_result, "r") as f:
        expected_schedule_string = f.read()

    with open(filename_output, "r") as f:
        schmerge_output = f.read()

    assert schedule_string == expected_schedule_string
    assert schmerge_output == schedule_string
    # Check if result and expected result are equal
