from __future__ import absolute_import
import datetime
import pytest
from collections import namedtuple

from ecl.summary import EclSum

from spinningjenny import valid_ecl_file, valid_date
from spinningjenny.extract_summary_data import (
    validate_arguments,
    apply_calculation,
    extract_value,
    CalculationType,
)
from tests import tmpdir, relpath, MockParser


TEST_DATA_PATH = relpath("tests", "testdata", "extract_summary_data")
Options = namedtuple(
    "Options",
    ("summary", "start_date", "end_date", "type", "key", "percentile", "multiplier"),
)


@pytest.fixture
@tmpdir(TEST_DATA_PATH)
def defaults():
    parser = MockParser()
    return (
        Options(
            summary=valid_ecl_file("REEK-0", parser),
            start_date=valid_date("2000-01-01", parser),
            end_date=valid_date("2003-01-01", parser),
            type="max",
            key="FGPT",
            percentile=95,
            multiplier=1,
        ),
        parser,
    )


@pytest.fixture
def ecl_sum():
    sum_keys = {"FOPT": [2, 22, 52, 72, 82, 82], "FOPR": [2, 4, 6, 4, 2, 0]}
    dimensions = [10, 10, 10]
    ecl_sum = EclSum.writer("TEST", datetime.date(2000, 1, 1), *dimensions)

    for key in sum_keys:
        ecl_sum.add_variable(key, wgname=None, num=0)

    for idx in range(6):
        t_step = ecl_sum.add_t_step(idx, 5 * idx)
        for key, item in sum_keys.items():
            t_step[key] = item[idx]

    return ecl_sum


def test_validate_arguments(defaults):
    options, parser = defaults
    validate_arguments(options, parser)
    assert parser.get_error() is None

    validate_arguments(options._replace(start_date=None), parser)
    assert parser.get_error() is None

    validate_arguments(
        options._replace(start_date=None, end_date=datetime.date(2002, 1, 4)), parser
    )
    assert (
        "Date 2002-01-04 is not part of the simulation report dates"
        in parser.get_error()
    )

    validate_arguments(options._replace(key="NULL"), parser)
    assert "Missing required data NULL in summary file." in parser.get_error()

    start_date = options.start_date
    end_date = options.end_date
    validate_arguments(
        options._replace(start_date=end_date, end_date=start_date), parser
    )
    assert "Start date is after end date." in parser.get_error()

    validate_arguments(options._replace(start_date=datetime.date(1990, 1, 1)), parser)
    assert (
        "Date 1990-01-01 is not part of the simulation report dates"
        in parser.get_error()
    )
    validate_arguments(options._replace(end_date=datetime.date(2004, 1, 1)), parser)
    assert (
        "Date 2004-01-01 is not part of the simulation report dates"
        in parser.get_error()
    )


def test_apply_calculation(ecl_sum):
    start_date = datetime.date(2000, 1, 1)
    end_date = datetime.date(2000, 1, 21)
    calc_type = CalculationType.MAX
    key = "FOPT"

    result = apply_calculation(ecl_sum, calc_type, key, start_date, end_date)
    expected_result = 82
    assert result == expected_result

    calc_type = CalculationType.DIFF
    result = apply_calculation(ecl_sum, calc_type, key, start_date, end_date)
    expected_result = 80
    assert result == expected_result


def test_extract_value(ecl_sum):
    result = extract_value(ecl_sum, "FOPR", datetime.date(2000, 1, 16))
    expected_result = 4
    assert result == expected_result

    result = extract_value(ecl_sum, "FOPT", datetime.date(2000, 1, 11))
    expected_result = 52
    assert result == expected_result
