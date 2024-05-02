from copy import deepcopy
from typing import Any, Dict, Set

import pytest
from everest_models.jobs.fm_well_swapping.model_config import (
    SINGLE_WORD,
    ConfigSchema,
    DircetionalState,
    Scaling,
    State,
    validate_priorities_and_state_initial_same_wells,
)
from everest_models.jobs.shared.io_utils import load_yaml
from hypothesis import given
from hypothesis import strategies as st
from pydantic import ValidationError
from sub_testdata import WELL_SWAPPING as TEST_DATA


@pytest.fixture(scope="module")
def well_swap_config_data(path_test_data) -> Dict[str, Any]:
    return load_yaml(path_test_data / TEST_DATA / "well_swap_config.yml")


@pytest.mark.parametrize(
    "source, target, match",
    (
        pytest.param([5, 4.6], [0, 1], r"1.*\s+source", id="source"),
        pytest.param([0, 1], [5, 4.9], r"1.*\s+target", id="target"),
        pytest.param([1, 0.5], [5, 4.9], r"2.*\s+source\s+.*\s+.*\s+target", id="both"),
    ),
)
def test_well_swapping_config_scaling_bad(source, target, match) -> None:
    with pytest.raises(ValidationError, match=match):
        Scaling.model_validate({"source": source, "target": target})


@given(st.from_regex(regex=SINGLE_WORD, fullmatch=True))
def test_well_swapping_config_state_action_bad(value) -> None:
    assert DircetionalState.model_validate({"source": value, "target": "other"})
    assert DircetionalState.model_validate({"source": "other", "target": value})


def test_well_swapping_config_state_action_same_target_source() -> None:
    with pytest.raises(ValidationError, match="source and values cannot be the same"):
        DircetionalState.model_validate({"source": "same", "target": "same"})


@pytest.mark.parametrize(
    "initial",
    (
        pytest.param({"A": "one", "B": "one", "C": "one"}, id="one viable state used"),
        pytest.param(
            {"A": "three", "B": "two", "C": "three"}, id="two viable state used"
        ),
        pytest.param(
            {"A": "one", "B": "two", "C": "three"}, id="all viable state used"
        ),
    ),
)
def test_well_swapping_config_state_initial_in_viable(initial) -> None:
    assert (
        state := State.model_validate(
            {"viable": ["one", "two", "three"], "initial": initial}
        )
    )
    assert state.wells == ("A", "B", "C")


def test_well_swapping_config_state_initial_not_in_viable() -> None:
    with pytest.raises(ValidationError, match="Non-viable status given"):
        State.model_validate(
            {
                "viable": ["one", "two"],
                "initial": {"A": "one", "B": "three", "C": "four"},
            }
        )


@pytest.mark.parametrize(
    "constraint", ("n_max_wells", "n_switch_states", "state_duration")
)
def test_well_swapping_config_constraints_bad(
    constraint: str,
    well_swap_config_data: Dict[str, Any],
) -> None:
    config = deepcopy(well_swap_config_data)
    config["constraints"][constraint]["fallback_values"].pop()
    with pytest.raises(
        ValidationError, match="Fallback values are not the same length"
    ):
        ConfigSchema.model_validate(config)


@pytest.mark.parametrize(
    "priority_wells, initial_wells",
    (
        pytest.param(set(), {"one"}, id="no priority wells"),
        pytest.param({"one"}, set(), id="no initial wells"),
        pytest.param(set(), set(), id="no wells"),
        pytest.param({"one"}, {"one"}, id="same wells"),
    ),
)
def test_validate_priorities_and_state_initial_same_wells(
    priority_wells: Set[str], initial_wells: Set[str]
) -> None:
    assert (
        validate_priorities_and_state_initial_same_wells(priority_wells, initial_wells)
        is None
    )


def test_validate_priorities_and_state_initial_same_wells_fault() -> None:
    with pytest.raises(
        ValueError,
        match="There are some discrepancies in `properties` and/or `initial_states`",
    ):
        validate_priorities_and_state_initial_same_wells(
            {"one", "two"}, {"one", "three"}
        )
