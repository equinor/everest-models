import logging
from textwrap import dedent
from typing import Dict

import pytest
from everest_models.jobs.fm_well_swapping.models.state import Quota, State
from everest_models.jobs.fm_well_swapping.state_processor import StateProcessor


def test_locked_state_first_iteration(
    well_swapping_state_processor: StateProcessor, monkeypatch: pytest.MonkeyPatch
) -> None:
    with monkeypatch.context() as patch:
        patch.setattr(well_swapping_state_processor, "_locked", True)
        assert well_swapping_state_processor.is_locked
        with pytest.raises(
            RuntimeError,
            match=dedent(
                """\
                A state lock was found on the first iteration.
                current state map:
                        open  closed  locked
                open       1       1       0
                closed     1       1       0
                locked     1       0       1
                Please check the states section in your configuration."""
            ),
        ):
            well_swapping_state_processor.latest_valid_states(0)


def test_locked_state_with_history(
    well_swapping_state_processor: StateProcessor,
    caplog: pytest.LogCaptureFixture,
) -> None:
    well_swapping_state_processor.process(
        ["one", "two", "three", "four"], "open", {"open": 2, "closed": 4, "locked": 4}
    )
    assert not well_swapping_state_processor.is_locked
    with caplog.at_level(logging.WARNING):
        well_swapping_state_processor.process(
            ["three", "two", "one", "four"],
            "closed",
            {"open": 1, "closed": 0, "locked": 0},
        )
    # assert "Encouter a state lock." in caplog.text
    assert well_swapping_state_processor.is_locked
    assert dict(well_swapping_state_processor.latest_valid_states(2)) == {
        "one": "open",
        "two": "open",
        "three": "locked",
        "four": "locked",
    }


def test_process_bad_cases(
    well_swapping_state_processor: StateProcessor,
    well_swapping_quotas: Dict[State, Quota],
) -> None:
    with pytest.raises(
        ValueError, match="Case names must be a subset of initial state cases"
    ):
        well_swapping_state_processor.process(
            ["unknown_case"], "don't matter", well_swapping_quotas
        )
