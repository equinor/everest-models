from textwrap import dedent
from typing import Any, Dict, Optional

import pytest

from everest_models.jobs.fm_well_swapping.models.state import StateConfig
from everest_models.jobs.fm_well_swapping.state_machine import State, StateMachine


@pytest.mark.parametrize(
    "data, expected",
    (
        pytest.param(
            {
                "hierarchy": ("open", "close"),
            },
            dedent(
                """\
                       open  close
                open      1      1
                close     1      1"""
            ),
            id="binary states",
        ),
        pytest.param(
            {"hierarchy": ("open", "close"), "allow_inactions": False},
            dedent(
                """\
                       open  close
                open      0      1
                close     1      0"""
            ),
            id="binary states force action",
        ),
        pytest.param(
            {
                "hierarchy": ("open", "close", "locked"),
                "actions": (("open", "locked"),),
                "forbiden_actions": True,
            },
            dedent(
                """\
                        open  close  locked
                open       1      1       0
                close      1      1       1
                locked     1      1       1"""
            ),
            id="forbiden actions tri-state",
        ),
        pytest.param(
            {
                "hierarchy": ("open", "close", "locked"),
                "actions": (("open", "locked"), ("close", "open")),
            },
            dedent(
                """\
                        open  close  locked
                open       1      0       1
                close      1      1       0
                locked     0      0       1"""
            ),
            id="allowed actions tri-state",
        ),
        pytest.param(
            {
                "hierarchy": ("open", "close", "locked"),
                "actions": (("open", "locked"), ("close", "open")),
                "allow_inactions": False,
            },
            dedent(
                """\
                        open  close  locked
                open       0      0       1
                close      1      0       0
                locked     0      0       0"""
            ),
            id="tri-state force action",
        ),
        pytest.param(
            {
                "hierarchy": ("open", "close", "locked", "broken"),
                "actions": (
                    ("open", "locked"),
                    ("locked", "open"),
                    ("locked", "locked"),
                ),
                "forbiden_actions": True,
            },
            dedent(
                """\
                        open  close  locked  broken
                open       1      1       0       1
                close      1      1       1       1
                locked     0      1       0       1
                broken     1      1       1       1"""
            ),
            id="covers more than tri-state",
        ),
    ),
)
def test_state_machine_from_config(data: Dict[str, Any], expected: str) -> None:
    data["hierarchy"] = tuple({"label": state} for state in data["hierarchy"])
    state_machine = StateMachine.from_config(StateConfig.model_validate(data))
    assert isinstance(state_machine, StateMachine), (
        "Should correctly build a StateMachine instance."
    )
    assert str(state_machine) == expected, "State machines matrix should match"


@pytest.mark.parametrize(
    "source, target, expected",
    (
        pytest.param("open", "closed", True, id="Direct transition available"),
        pytest.param("closed", "ajar", False, id="Target state doesn't exist"),
        pytest.param("open", "locked", False, id="Target state not available"),
        pytest.param("ajar", "closed", False, id="source state doesn't exist"),
    ),
)
def test_is_possible_action(
    well_swapping_state_machine: StateMachine,
    source: State,
    target: State,
    expected: Optional[State],
) -> None:
    assert well_swapping_state_machine.is_possible_action(source, target) == expected, (
        "Should be able to check state matrix for executable action"
    )


def test_empty_state_map() -> None:
    assert not (
        StateMachine([], (), False, True).is_possible_action("open", "closed")
    ), "Should handle empty state matrix gracefully"


@pytest.mark.parametrize(
    "state, expected",
    (
        pytest.param("open", "closed", id="open"),
        pytest.param("closed", "open", id="closed"),
        pytest.param("locked", "closed", id="locked"),
    ),
)
def test_next_possible_action(
    well_swapping_state_machine: StateMachine, state: State, expected: State
) -> None:
    assert well_swapping_state_machine.next_possible_action("open", state) == (
        "open",
        expected,
    ), "Should be able to get the next possible state in matrix"
