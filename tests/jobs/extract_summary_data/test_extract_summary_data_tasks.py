import datetime
from collections import namedtuple

from summary import ecl_summary
from utils import MockParser

from spinningjenny.jobs.fm_extract_summary_data.utils import (
    CalculationType,
    apply_calculation,
    extract_value,
    validate_arguments,
)
from spinningjenny.jobs.shared.validators import valid_date

Options = namedtuple(
    "Options",
    ("summary", "start_date", "end_date", "type", "key", "percentile", "multiplier"),
)


def test_validate_arguments():
    parser = MockParser()
    options = Options(
        summary=ecl_summary(),
        start_date=valid_date("2000-01-01", parser),
        end_date=valid_date("2000-01-26", parser),
        type="max",
        key="FOPT",
        percentile=95,
        multiplier=1,
    )
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


def test_apply_calculation():
    start_date = datetime.date(2000, 1, 1)
    end_date = datetime.date(2000, 1, 21)
    calc_type = CalculationType.MAX
    key = "FOPT"

    result = apply_calculation(ecl_summary(), calc_type, key, start_date, end_date)
    expected_result = 82
    assert result == expected_result

    calc_type = CalculationType.DIFF
    result = apply_calculation(ecl_summary(), calc_type, key, start_date, end_date)
    expected_result = 80
    assert result == expected_result


def test_extract_value():
    result = extract_value(ecl_summary(), "FOPR", datetime.date(2000, 1, 16))
    expected_result = 4
    assert result == expected_result

    result = extract_value(ecl_summary(), "FOPT", datetime.date(2000, 1, 11))
    expected_result = 52
    assert result == expected_result
