from typing import Any, Dict, Tuple

import pytest
from pydantic import ValidationError
from sub_testdata import WELL_SWAPPING as TEST_DATA

from everest_models.jobs.fm_well_swapping.models import StateConfig
from everest_models.jobs.shared.io_utils import load_yaml


@pytest.fixture(scope="module")
def well_swap_config_data(path_test_data) -> Dict[str, Any]:
    return load_yaml(path_test_data / TEST_DATA / "well_swap_config.yml")


@pytest.fixture(scope="module")
def well_swap_state_hierarchy() -> Tuple[Dict[str, str], ...]:
    return {"label": "high"}, {"label": "middle"}, {"label": "low"}


@pytest.mark.parametrize(
    "input, expected",
    (
        pytest.param(None, ("high",) * 4, id="states is None"),
        pytest.param("middle", ("middle",) * 4, id="initial state as a string"),
        pytest.param(
            ("middle", "middle"),
            ("middle", "middle", "high", "high"),
            id="fill missing tail",
        ),
        pytest.param(
            ("_", "middle"),
            ("high", "middle", "high", "high"),
            id="fill _ default alias",
        ),
        pytest.param(
            ("middle",) * 5,
            ("middle",) * 4,
            id="fill None default alias",
        ),
    ),
)
def test_targets(input, expected, well_swap_state_hierarchy) -> None:
    assert (
        state := StateConfig.model_validate(
            {"hierarchy": well_swap_state_hierarchy, "targets": input}
        )
    )
    assert state.get_targets(4) == expected


@pytest.mark.parametrize(
    "input, expected",
    (
        pytest.param(
            None, {"A": "low", "B": "low", "C": "low"}, id="initial states is None"
        ),
        pytest.param(
            "middle",
            {"A": "middle", "B": "middle", "C": "middle"},
            id="initial state as a string",
        ),
        pytest.param(
            {"A": "middle"},
            {"A": "middle", "B": "low", "C": "low"},
            id="fill default when omited",
        ),
        pytest.param(
            {"A": "middle", "B": "high"},
            {"A": "middle", "B": "high", "C": "low"},
            id="multiple initial states",
        ),
    ),
)
def test_get_initial_state(input, expected, well_swap_state_hierarchy) -> None:
    assert (
        state := StateConfig.model_validate(
            {"hierarchy": well_swap_state_hierarchy, "initial": input}
        )
    )
    assert state.get_initial(set("ABC")) == expected


def test_defualt_values(well_swap_state_hierarchy) -> None:
    assert (
        state := StateConfig.model_validate({"hierarchy": well_swap_state_hierarchy})
    )
    assert state.get_initial(set("ABC")) == {"A": "low", "B": "low", "C": "low"}
    assert state.get_targets(4) == ("high",) * 4
    assert list(state.get_quotas(4, 3)) == [{"low": 3, "middle": 3, "high": 3}] * 4


@pytest.mark.parametrize(
    "data",
    (
        pytest.param({"initial": "four"}, id="initial"),
        pytest.param({"targets": "four"}, id="targets"),
    ),
)
def test_well_swapping_config_state_not_in_hierarcy(
    data, well_swap_state_hierarchy
) -> None:
    with pytest.raises(ValidationError, match="State not in hierarchy"):
        StateConfig.model_validate({"hierarchy": well_swap_state_hierarchy, **data})
