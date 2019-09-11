from __future__ import absolute_import
import datetime
import pytest
from collections import namedtuple

from spinningjenny import valid_ecl_file, valid_date
from spinningjenny.extract_summary_data import (
    valid_percentile,
    validate_arguments,
    apply_calculation,
    extract_value,
)
from tests import tmpdir, relpath, MockParser


TEST_DATA_PATH = relpath("tests", "testdata", "stripdates")
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


def test_valid_percentile():
    parser = MockParser()
    valid_percentile("43", parser)
    assert parser.get_error() is None

    valid_percentile(43, parser)
    assert parser.get_error() is None

    parser = MockParser()
    valid_percentile("-1", parser)
    assert "Percentile value -1.0 not in range [0,100]" in parser.get_error()

    parser = MockParser()
    valid_percentile("101", parser)
    assert "Percentile value 101.0 not in range [0,100]" in parser.get_error()


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
        "Cannot extract key FGPT value for date 2002-01-04 not part of the simulation report dates"
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
        "Start date 1990-01-01 is not in the simulation time interval [1999-12-01, 2003-01-01]"
        in parser.get_error()
    )
    validate_arguments(options._replace(end_date=datetime.date(2004, 1, 1)), parser)
    assert (
        "End date 2004-01-01 is not in the simulation time interval [1999-12-01, 2003-01-01]"
        in parser.get_error()
    )


def test_apply_calculation(defaults):
    options, parser = defaults
    validate_arguments(options, parser)
    assert parser.get_error() is None

    result = apply_calculation(options)
    expected_result = 1848592.0
    assert result == expected_result


def test_extract_value(defaults):
    options, parser = defaults
    options = options._replace(start_date=None, end_date=datetime.date(2001, 4, 1))
    validate_arguments(options, parser)
    assert parser.get_error() is None

    result = extract_value(options.summary, options.key, options.end_date)
    expected_result = 1157883.875
    assert result == expected_result
