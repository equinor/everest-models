import datetime
from re import escape

import pytest
from utils import MockParser, relpath, tmpdir

from spinningjenny.jobs.fm_select_wells.tasks import select_wells
from spinningjenny.jobs.utils.validators import valid_json_file

TEST_DATA_PATH = relpath("tests", "testdata", "select_wells")


@tmpdir(TEST_DATA_PATH)
def test_select_wells():
    parser = MockParser()
    input = valid_json_file("input.json", parser)
    wells_number = next(iter(valid_json_file("well_number.json", parser).values()))
    output = select_wells(input, wells_number, [0.0, 47.0], [0.0, 1.0])
    expected = valid_json_file("expected_result.json", parser)
    assert output == expected


@tmpdir(TEST_DATA_PATH)
def test_select_wells_n():
    parser = MockParser()
    input = valid_json_file("input.json", parser)
    output = select_wells(input, 2)
    expected = valid_json_file("expected_result.json", parser)
    assert output == expected


@tmpdir(TEST_DATA_PATH)
def test_select_wells_real_bounds_error():
    parser = MockParser()
    input = valid_json_file("input.json", parser)
    with pytest.raises(ValueError, match=escape("Invalid real bounds: [47.0, 0.0]")):
        select_wells(input, 1, [47.0, 0.0], [0.0, 1.0])


@tmpdir(TEST_DATA_PATH)
def test_select_wells_scaled_bounds_error():
    parser = MockParser()
    input = valid_json_file("input.json", parser)
    with pytest.raises(ValueError, match=escape("Invalid scaled bounds: [1.0, 0.0]")):
        select_wells(input, 1, [0.0, 47.0], [1.0, 0.0])


@tmpdir(TEST_DATA_PATH)
def test_select_wells_too_many_wells_error():
    parser = MockParser()
    input = valid_json_file("input.json", parser)
    with pytest.raises(ValueError, match=escape("Too many wells requested (47).")):
        select_wells(input, 1, [0.0, 47.0], [0.0, 1.0])


@tmpdir(TEST_DATA_PATH)
def test_select_wells_max_date():
    parser = MockParser()
    input = valid_json_file("input.json", parser)
    output = select_wells(
        input, 100, max_date=datetime.date.fromisoformat("2023-03-01")
    )
    expected = valid_json_file("expected_result.json", parser)
    assert output == expected


@tmpdir(TEST_DATA_PATH)
def test_select_wells_max_date_n_none():
    parser = MockParser()
    input = valid_json_file("input.json", parser)
    output = select_wells(
        input, None, max_date=datetime.date.fromisoformat("2023-03-01")
    )
    expected = valid_json_file("expected_result.json", parser)
    assert output == expected


@tmpdir(TEST_DATA_PATH)
def test_select_wells_max_date_exact():
    parser = MockParser()
    input = valid_json_file("input.json", parser)
    output = select_wells(
        input, 100, max_date=datetime.date.fromisoformat("2023-01-21")
    )
    expected = valid_json_file("expected_result.json", parser)
    assert output == expected


@tmpdir(TEST_DATA_PATH)
def test_select_wells_max_date_not_needed():
    parser = MockParser()
    input = valid_json_file("input.json", parser)
    wells_number = next(iter(valid_json_file("well_number.json", parser).values()))
    output = select_wells(
        input,
        wells_number,
        [0.0, 47.0],
        [0.0, 1.0],
        datetime.date.fromisoformat("2023-07-01"),
    )
    expected = valid_json_file("expected_result.json", parser)
    assert output == expected


@tmpdir(TEST_DATA_PATH)
def test_select_wells_max_date_not_needed_n():
    parser = MockParser()
    input = valid_json_file("input.json", parser)
    output = select_wells(input, 2, max_date=datetime.date.fromisoformat("2023-07-01"))
    expected = valid_json_file("expected_result.json", parser)
    assert output == expected


@tmpdir(TEST_DATA_PATH)
def test_select_wells_max_date_same_dates():
    parser = MockParser()
    input = valid_json_file("input.json", parser)
    output = select_wells(input, 3, max_date=datetime.date.fromisoformat("2023-03-13"))
    assert len(output) == 3
    assert output[2]["name"] == "WELL3"


@tmpdir(TEST_DATA_PATH)
def test_select_wells_max_date_same_dates_reversed():
    parser = MockParser()
    input = valid_json_file("input.json", parser)
    input = input[:2] + input[3:] + [input[2]]
    output = select_wells(input, 3, max_date=datetime.date.fromisoformat("2023-03-13"))
    assert len(output) == 3
    assert output[2]["name"] == "WELL4"
