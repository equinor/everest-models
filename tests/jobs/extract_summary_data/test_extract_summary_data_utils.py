import argparse
import datetime
from collections import namedtuple

import pytest
from summary import ecl_summary

from everest_models.jobs.fm_extract_summary_data.parser import (
    _parse_keyword_entry,
    _parse_section,
)
from everest_models.jobs.fm_extract_summary_data.tasks import (
    CalculationType,
    extract_static_targets,
    extract_value,
    validate_arguments,
)


@pytest.fixture(scope="module")
def validate_argument_options():
    return namedtuple(
        "Options",
        ("summary", "start_date", "end_date", "type", "key"),
    )(
        summary=ecl_summary(),
        start_date=datetime.date.fromisoformat("2000-01-01"),
        end_date=datetime.date.fromisoformat("2000-01-26"),
        type=CalculationType.MAX,
        key="FOPT",
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
    summary, _, _, _, key = validate_argument_options
    assert extract_value(summary, "FOPR", datetime.date(2000, 1, 16)) == 4
    assert extract_value(summary, key, datetime.date(2000, 1, 11)) == 52


@pytest.mark.parametrize(
    ("calculation_type", "expected"),
    [
        (CalculationType.MAX, 10),
        (CalculationType.MIN, 2),
        (CalculationType.MEAN, 6),
        (CalculationType.MEDIAN, 6),
        (CalculationType.DIFF, 8),
    ],
)
def test_calculation_type_extract(calculation_type, expected):
    summary = ecl_summary()

    assert (
        calculation_type.extract(
            summary,
            key="FGPT",
            start_date=datetime.date(2000, 1, 1),
            end_date=datetime.date(2000, 1, 26),
        )
        == expected
    )


def test_parse_section_parses_fip_region():
    section = _parse_section(
        {
            "fip-key": "fipnum",
            "fip-region": {
                "region-number": 2,
                "output": "target.txt",
                "aggregation": "max",
                "key": "FOPT",
                "unit-conversion": 1000,
            },
        },
        index=1,
    )

    assert section.fip_key == "FIPNUM"
    assert len(section.fip_region) == 1
    assert section.fip_region[0].region_number == 2
    assert section.fip_region[0].unit_conversion == 1000


def test_parse_section_rejects_optimization_direction():
    with pytest.raises(ValueError, match="unsupported key.*optimization_direction"):
        _parse_section(
            {
                "fip-key": "FIPNUM",
                "fip-region": {
                    "region-number": 2,
                    "output": "target.txt",
                    "aggregation": "max",
                    "key": "FOPT",
                    "optimization_direction": "max",
                },
            },
            index=1,
        )


def test_extract_static_targets_uses_fip_region():
    requested_keys = []

    class Summary:
        start_time = datetime.datetime(2000, 1, 1)

        def __contains__(self, key):
            return key in {"FOPTNUM:2", "TIME"}

        def numpy_vector(self, key):
            requested_keys.append(key)
            return {"FOPTNUM:2": [2, 4, 8], "TIME": [0, 1, 2]}[key]

    targets = extract_static_targets(
        Summary(),
        {
            "fip-section": {
                "fip-key": "FIPNUM",
                "fip-region": {
                    "region-number": 2,
                    "output": "target.txt",
                    "aggregation": "max",
                    "key": "FOPT",
                    "unit-conversion": 2,
                },
            }
        },
    )

    assert requested_keys == ["FOPTNUM:2"]
    assert targets == {"target.txt": 4}


def test_extract_static_targets_supports_median_for_fip_region():
    class Summary:
        def __contains__(self, key):
            return key == "FOPTNUM:2"

        def numpy_vector(self, key):
            return {"FOPTNUM:2": [2, 4, 8]}[key]

    targets = extract_static_targets(
        Summary(),
        {
            "fip-section": {
                "fip-key": "FIPNUM",
                "fip-region": {
                    "region-number": 2,
                    "output": "target.txt",
                    "aggregation": "median",
                    "key": "FOPT",
                },
            }
        },
    )

    assert targets == {"target.txt": 4}


def test_extract_static_targets_uses_aggregation_over_entire_series():
    targets = extract_static_targets(
        ecl_summary(),
        {
            "key-section": {
                "key": "FGPT",
                "output": "target.txt",
                "aggregation": "max",
            }
        },
    )

    assert targets == {"target.txt": 10}


def test_extract_static_targets_limits_aggregation_to_date_interval():
    targets = extract_static_targets(
        ecl_summary(),
        {
            "key-section": {
                "key": "FGPT",
                "output": "target.txt",
                "aggregation": "mean",
                "start-date": "2000-01-01",
                "end-date": "2000-01-26",
            }
        },
    )

    assert targets == {"target.txt": 6}


def test_extract_static_targets_selects_output_date():
    targets = extract_static_targets(
        ecl_summary(),
        {
            "key-section": {
                "key": "FGPT",
                "output": "target.txt",
                "output-date": "2000-01-21",
            }
        },
    )

    assert targets == {"target.txt": 8}


def test_parse_keyword_entry_rejects_non_aggregation_type():
    with pytest.raises(
        ValueError, match="aggregation must be min, max, mean, or median"
    ):
        _parse_keyword_entry(
            {
                "key": "FGPT",
                "output": "target.txt",
                "aggregation": "diff",
            },
            index=1,
        )


def test_parse_keyword_entry_rejects_type_field():
    with pytest.raises(ValueError, match="unsupported key.*type"):
        _parse_keyword_entry(
            {
                "key": "FGPT",
                "output": "target.txt",
                "type": "min",
            },
            index=1,
        )


def test_parse_keyword_entry_rejects_aggregation_with_output_date():
    with pytest.raises(ValueError, match="use either 'aggregation' or 'output-date'"):
        _parse_keyword_entry(
            {
                "key": "FGPT",
                "output": "target.txt",
                "aggregation": "max",
                "output-date": "2000-01-21",
            },
            index=1,
        )


def test_extract_static_targets_uses_last_value_for_fip_region_without_type():
    class Summary:
        def __contains__(self, key):
            return key == "FOPTNUM:2"

        def numpy_vector(self, key):
            return {"FOPTNUM:2": [2, 4, 8]}[key]

    targets = extract_static_targets(
        Summary(),
        {
            "fip-section": {
                "fip-key": "FIPNUM",
                "fip-region": {
                    "region-number": 2,
                    "output": "target.txt",
                    "key": "FOPT",
                },
            }
        },
    )

    assert targets == {"target.txt": 8}


def test_extract_static_targets_accepts_o_as_output_alias():
    class Summary:
        def __contains__(self, key):
            return key == "FGIT"

        def numpy_vector(self, key):
            return {"FGIT": [2, 4, 8]}[key]

    targets = extract_static_targets(
        Summary(),
        {
            "key-section": {
                "key": "FGIT",
                "o": "target.txt",
            }
        },
    )

    assert targets == {"target.txt": 8}


def test_extract_static_targets_accepts_key_for_keyword_section():
    class Summary:
        def __contains__(self, key):
            return key == "FOPT"

        def numpy_vector(self, key):
            return {"FOPT": [2, 4, 8]}[key]

    targets = extract_static_targets(
        Summary(),
        {
            "key-section": {
                "key": "FOPT",
                "output": "target.txt",
                "aggregation": "max",
            }
        },
    )

    assert targets == {"target.txt": 8}


def test_extract_static_targets_uses_last_value_without_selection():
    class Summary:
        def __contains__(self, key):
            return key == "FGIT"

        def numpy_vector(self, key):
            return {"FGIT": [2, 4, 8]}[key]

    targets = extract_static_targets(
        Summary(),
        {
            "key-section": {
                "key": "FGIT",
                "output": "target.txt",
            }
        },
    )

    assert targets == {"target.txt": 8}
