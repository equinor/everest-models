import copy

import pytest
from pydantic import ValidationError

from everest_models.jobs.fm_well_constraints.models import (
    WellConstraintConfig,
)
from everest_models.jobs.fm_well_constraints.models.config import Phase, Tolerance

_WELL_CONSTRAINTS_CONFIG = {
    "INJECT1": {
        1: {
            "rate": {
                "value": 500,
            },
            "phase": {
                "options": [
                    "gas",
                    "water",
                ],
            },
            "duration": {
                "value": 13,
            },
        }
    }
}

_WELL_CONSTRAINTS_CONFIG_ERRORS = [
    "Either ['max', 'min'] PAIR or 'value' key, but not both.",
    "'max' and 'min' must be in a pair",
    "'max' cannot be less or equal to 'min' value.",
]


def assert_error_messages(info: pytest.ExceptionInfo, *msgs):
    errors = info.value.errors()

    assert len(errors) == len(msgs)
    assert all(error["msg"].replace("Value error, ", "") in msgs for error in errors)


def copy_config_constraint() -> dict:
    return copy.deepcopy(_WELL_CONSTRAINTS_CONFIG)


def test_constraints_config_model_fields():
    assert WellConstraintConfig.model_validate(_WELL_CONSTRAINTS_CONFIG)


def test_constraints_config_model_fields_min_error():
    config = copy.deepcopy(_WELL_CONSTRAINTS_CONFIG)
    config["INJECT1"][1]["rate"]["min"] = 0
    with pytest.raises(
        ValidationError,
        match="Well constrains job no longer supports scaled optimizer values",
    ):
        WellConstraintConfig.model_validate(config)


def test_constraints_config_model_fields_max_error():
    config = copy.deepcopy(_WELL_CONSTRAINTS_CONFIG)
    config["INJECT1"][1]["rate"]["max"] = 100
    with pytest.raises(
        ValidationError,
        match="Well constrains job no longer supports scaled optimizer values",
    ):
        WellConstraintConfig.model_validate(config)


def test_constraint_config_model_fields_options_value_error():
    config = copy.deepcopy(_WELL_CONSTRAINTS_CONFIG)
    phase = config["INJECT1"][1]["phase"]
    phase["value"] = phase.get("options")[0]
    with pytest.raises(
        ValidationError,
        match="'options' key cannot be used in conjunction with 'value' key",
    ):
        WellConstraintConfig.model_validate(config)


def test_constraints_config_model_fields_multi_error_multi_message():
    config = copy.deepcopy(_WELL_CONSTRAINTS_CONFIG)
    config["INJECT1"][1]["rate"]["max"] = 100
    phase = config["INJECT1"][1]["phase"]
    phase["value"] = phase["options"][0]
    phase["options"] = []
    with pytest.raises(ValidationError) as e:
        WellConstraintConfig.model_validate(config)
    errors = e.value.errors()
    errors = [error["msg"] for error in errors]
    assert len(errors) == 2
    assert any("Empty 'options' list" in msg for msg in errors)
    assert any(
        "Remove min or max keys from well constraint config file." in msg
        for msg in errors
    )


@pytest.mark.parametrize(
    "optimizer_value, expected",
    ((0, "GAS"), (0.25, "GAS"), (0.5, "GAS"), (0.75, "WATER"), (1, "WATER")),
)
def test_constraint_phase_model_optimum_value(optimizer_value, expected):
    phase = Phase.model_validate(_WELL_CONSTRAINTS_CONFIG["INJECT1"][1]["phase"])
    assert phase.optimum_value(optimizer_value) == expected


def test_constraint_phase_model_optimum_value_none():
    assert Phase.model_validate({"value": "water"}).optimum_value(None) == "WATER"


@pytest.mark.parametrize(
    "optimizer_value, config_value, expected",
    ((0, 500, 500), (0.1, None, 0.1)),
)
def test_constraint_tolerance_model_optimum_value(
    optimizer_value, config_value, expected
):
    config = copy.deepcopy(_WELL_CONSTRAINTS_CONFIG["INJECT1"][1]["rate"])
    if config_value is None:
        config = {}
    else:
        config["value"] = config_value

    rate = Tolerance.model_validate(config)
    assert rate.optimum_value(optimizer_value) == expected


def test_invalid_min_max_fields_throws_validation_error():
    with pytest.raises(ValidationError) as e:
        Tolerance.model_validate({"min": "314s", "max": 200})
    assert_error_messages(
        e, "Input should be a valid number, unable to parse string as a number"
    )
    with pytest.raises(ValidationError) as e:
        Tolerance.model_validate({"min": 314, "max": "200f"})
    assert_error_messages(
        e, "Input should be a valid number, unable to parse string as a number"
    )


def test_constraint_tolerance_model_optimum_value_none():
    assert Tolerance.model_validate({"value": 314}).optimum_value(None) == 314
    assert Tolerance().optimum_value(None) is None
