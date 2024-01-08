import copy

import pytest
from everest_models.jobs.fm_well_constraints.models import (
    Constraints,
    WellConstraintConfig,
)
from everest_models.jobs.fm_well_constraints.models.config import Phase, Tolerance
from hypothesis import given
from hypothesis import strategies as st
from pydantic import ValidationError

_WELL_CONSTRAINTS_CONFIG = {
    "INJECT1": {
        1: {
            "rate": {
                "min": 0,
                "max": 1000,
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
    assert all(
        error["msg"].replace("Assertion failed, ", "") in msgs for error in errors
    )


def get_config_constraint(key: str, pop: bool, retain: bool = True) -> dict:
    config = copy.deepcopy(_WELL_CONSTRAINTS_CONFIG)
    rate = config["INJECT1"][1]["rate"]
    if retain:
        rate["value"] = rate.pop(key) if pop else rate.get(key)
    else:
        rate.pop(key)
    return config


@given(st.floats(max_value=1, min_value=0))
def test_constraint_model_fields(value):
    assert Constraints.model_validate({"Li": {1: value}, "Vi": {2: 0.35}})


@given(st.floats(min_value=1.0000000001))
def test_constraint_model_fields_over_zero_error(value):
    with pytest.raises(ValidationError) as e:
        Constraints.model_validate({"Li": {1: value}, "Vi": {2: 0.35}})
    assert_error_messages(
        e, f"Value(s) are not within bounds [0, 1]:\n\tLi -> 1 -> {value}"
    )


@given(st.floats(max_value=-0.0000000001))
def test_constraint_model_fields_under_zero_error(value):
    with pytest.raises(ValidationError) as e:
        Constraints.model_validate({"Li": {1: value}, "Vi": {2: 0.35}})
    assert_error_messages(
        e, f"Value(s) are not within bounds [0, 1]:\n\tLi -> 1 -> {value}"
    )


def test_constraint_model_fields_multi_error_one_message():
    with pytest.raises(ValidationError) as e:
        Constraints.model_validate({"Li": {1: -0.3}, "Vi": {2: 1.35}})
    assert_error_messages(
        e, "Value(s) are not within bounds [0, 1]:\n\tLi -> 1 -> -0.3\tVi -> 2 -> 1.35"
    )


def test_constraints_config_model_fields():
    assert WellConstraintConfig.model_validate(_WELL_CONSTRAINTS_CONFIG)


@pytest.mark.parametrize(
    "config",
    (
        pytest.param(get_config_constraint("min", pop=True, retain=False), id="max"),
        pytest.param(get_config_constraint("max", pop=True, retain=False), id="min"),
    ),
)
def test_constraints_config_model_fields_min_or_max_error(config):
    with pytest.raises(ValidationError) as e:
        WellConstraintConfig.model_validate(config)
    assert_error_messages(e, _WELL_CONSTRAINTS_CONFIG_ERRORS[1])


@pytest.mark.parametrize(
    "config, error_message",
    (
        pytest.param(
            get_config_constraint("min", pop=True),
            "\n".join(_WELL_CONSTRAINTS_CONFIG_ERRORS[:-1]),
            id="max_value",
        ),
        pytest.param(
            get_config_constraint("max", pop=True),
            "\n".join(_WELL_CONSTRAINTS_CONFIG_ERRORS[:-1]),
            id="min_value",
        ),
        pytest.param(
            get_config_constraint("min", pop=False),
            _WELL_CONSTRAINTS_CONFIG_ERRORS[0],
            id="max_min_value",
        ),
    ),
)
def test_constraints_config_model_fields_min_max_value_error(config, error_message):
    with pytest.raises(ValidationError) as e:
        WellConstraintConfig.model_validate(config)
    assert_error_messages(e, error_message)


def test_constraint_config_model_fields_options_value_error():
    config = copy.deepcopy(_WELL_CONSTRAINTS_CONFIG)
    phase = config["INJECT1"][1]["phase"]
    phase["value"] = phase.get("options")[0]
    with pytest.raises(ValidationError) as e:
        WellConstraintConfig.model_validate(config)
    assert_error_messages(
        e, "'options' key cannot be used in conjunction with 'value' key."
    )


def test_constraints_config_model_fields_min_gt_max_error():
    config = copy.deepcopy(_WELL_CONSTRAINTS_CONFIG)
    rate = config["INJECT1"][1]["rate"]
    rate["max"] = rate["min"]
    with pytest.raises(ValidationError) as e:
        WellConstraintConfig.model_validate(config)
    assert_error_messages(e, _WELL_CONSTRAINTS_CONFIG_ERRORS[-1])


def test_constraints_config_model_fields_multi_error_one_message():
    config = get_config_constraint("min", pop=False)
    rate = config["INJECT1"][1]["rate"]
    rate["max"] = rate["min"]
    with pytest.raises(ValidationError) as e:
        WellConstraintConfig.model_validate(config)
    assert_error_messages(e, "\n".join(_WELL_CONSTRAINTS_CONFIG_ERRORS[::2]))


def test_constraints_config_model_fields_multi_error_multi_message():
    config = get_config_constraint("min", pop=False)
    phase = config["INJECT1"][1]["phase"]
    phase["value"] = phase["options"][0]
    phase["options"] = []
    with pytest.raises(ValidationError) as e:
        WellConstraintConfig.model_validate(config)
    assert_error_messages(e, "Empty 'options' list", _WELL_CONSTRAINTS_CONFIG_ERRORS[0])


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
    "optimizer_value, expected",
    ((0, 0), (0.1, 100), (0.2, 200), (0.15684, 156.84), (1, 1000)),
)
def test_constraint_tolerance_model_optimum_value(optimizer_value, expected):
    phase = Tolerance.model_validate(_WELL_CONSTRAINTS_CONFIG["INJECT1"][1]["rate"])
    assert phase.optimum_value(optimizer_value) == expected


def test_constraint_tolerance_model_optimum_value_none():
    assert Tolerance.model_validate({"value": 314}).optimum_value(None) == 314
    assert Tolerance().optimum_value(None) is None
