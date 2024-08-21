import argparse
import datetime
from collections import namedtuple

import pytest
from summary import ecl_summary

from everest_models.jobs.fm_extract_summary_data.tasks import (
    CalculationType,
    extract_value,
    validate_arguments,
)


@pytest.fixture(scope="module")
def validate_argument_options():
    return namedtuple(
        "Options",
        ("summary", "start_date", "end_date", "type", "key", "multiplier"),
    )(
        summary=ecl_summary(),
        start_date=datetime.date.fromisoformat("2000-01-01"),
        end_date=datetime.date.fromisoformat("2000-01-26"),
        type=CalculationType.MAX,
        key="FOPT",
        multiplier=1,
    )


class TestCaseValidateArgument:
    def test_validate_arguments(self, validate_argument_options):
        assert (
            validate_arguments(validate_argument_options) == validate_argument_options
        )

    def test_validate_arguments_no_start_date(self, validate_argument_options):
        options = validate_argument_options._replace(start_date=None)
        assert validate_arguments(options) == options

    def test_validate_arguments_no_start_date_end_date_not_in_summary(
        self,
        validate_argument_options,
    ):
        with pytest.raises(
            argparse.ArgumentTypeError,
            match="End date '2002-01-04' is not part of the simulation report dates",
        ):
            validate_arguments(
                validate_argument_options._replace(
                    start_date=None, end_date=datetime.date(2002, 1, 4)
                )
            )

    def test_validate_arguments_missing_key(self, validate_argument_options):
        with pytest.raises(
            argparse.ArgumentTypeError,
            match="Missing required data NULL in summary file.",
        ):
            validate_arguments(validate_argument_options._replace(key="NULL"))

    def test_validate_arguments_start_after_end_date(self, validate_argument_options):
        with pytest.raises(
            argparse.ArgumentTypeError,
            match=r"Start date '\d{4}-\d{2}-\d{2}' is after end date '\d{4}-\d{2}-\d{2}'.",
        ):
            validate_arguments(
                validate_argument_options._replace(
                    start_date=validate_argument_options.end_date,
                    end_date=validate_argument_options.start_date,
                )
            )

    def test_validate_arguments_start_date_not_in_summary(
        self, validate_argument_options
    ):
        with pytest.raises(
            argparse.ArgumentTypeError,
            match="Start date '1990-01-01' is not part of the simulation report dates",
        ):
            validate_arguments(
                validate_argument_options._replace(start_date=datetime.date(1990, 1, 1))
            )

    def test_validate_arguments_end_date_not_in_summary(
        self, validate_argument_options
    ):
        with pytest.raises(
            argparse.ArgumentTypeError,
            match="End date '2004-01-01' is not part of the simulation report dates",
        ):
            validate_arguments(
                validate_argument_options._replace(end_date=datetime.date(2004, 1, 1))
            )

    def test_validate_arguments_multiple_errors(self, validate_argument_options):
        with pytest.raises(
            argparse.ArgumentTypeError,
            match=r"Start date '\d{4}-\d{2}-\d{2}' is after end date '\d{4}-\d{2}-\d{2}'.",
        ) as e:
            validate_arguments(
                validate_argument_options._replace(
                    start_date=datetime.date(2022, 11, 7),
                    end_date=datetime.date(2004, 1, 1),
                )
            )
        error_message = str(e.value)
        assert (
            "End date '2004-01-01' is not part of the simulation report dates"
            in error_message
        )
        assert (
            "Start date '2022-11-07' is not part of the simulation report dates"
            in error_message
        )


def test_extract_value(validate_argument_options):
    summary, _, _, _, key, _ = validate_argument_options
    assert extract_value(summary, "FOPR", datetime.date(2000, 1, 16)) == 4
    assert extract_value(summary, key, datetime.date(2000, 1, 11)) == 52
