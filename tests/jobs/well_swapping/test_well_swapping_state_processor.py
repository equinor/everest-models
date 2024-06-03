from textwrap import dedent
from typing import Dict, List

import pytest
from everest_models.jobs.fm_well_swapping.models.state import Case, Quota, State
from everest_models.jobs.fm_well_swapping.state_machine import StateMachine
from everest_models.jobs.fm_well_swapping.state_processor import StateProcessor


def test_locked_state(
    well_swapping_initial_state: Dict[Case, State],
    well_swapping_quotas: Dict[State, List[Quota]],
) -> None:
    processor = StateProcessor(
        state_machine=StateMachine(
            list(well_swapping_quotas),
            (("open", "locked"), ("closed", "locked"), ("locked", "closed")),
            forbiden=True,
            inaction=False,
        ),
        initial_states=well_swapping_initial_state,
        quotas=well_swapping_quotas,
    )

    with pytest.raises(
        ValueError,
        match=dedent(
            """\
            A state lock was found in your configuration.
            current state map:
                    open  closed  locked
            open       0       1       0
            closed     1       0       0
            locked     1       0       0
            Please look to your state section and correct it as needed."""
        ),
    ):
        processor.process(["one", "two", "three"], "open", 0)


def test_process_bad_cases(well_swapping_state_processor: StateProcessor) -> None:
    with pytest.raises(
        ValueError, match="Case names must be a subset of initial state cases"
    ):
        well_swapping_state_processor.process(["unknown_case"], "don't matter", 0)
