from typing import Dict, List

import pytest
from everest_models.jobs.fm_well_swapping.models import Case, Quota, State
from everest_models.jobs.fm_well_swapping.state_machine import StateMachine
from everest_models.jobs.fm_well_swapping.state_processor import StateProcessor


@pytest.fixture(scope="module")
def well_swapping_initial_state() -> Dict[Case, State]:
    return {"one": "locked", "two": "locked", "three": "locked", "four": "locked"}


@pytest.fixture(scope="module")
def well_swapping_quotas() -> Dict[State, Quota]:
    return {"open": 2, "closed": 4, "locked": 0}


@pytest.fixture(scope="module")
def well_swapping_state_machine(
    well_swapping_quotas: Dict[State, List[Quota]],
) -> StateMachine:
    return StateMachine(
        list(well_swapping_quotas),
        (("open", "locked"), ("closed", "locked"), ("locked", "closed")),
        forbiden=True,
        inaction=True,
    )


@pytest.fixture(scope="module")
def well_swapping_state_processor(
    well_swapping_state_machine: StateMachine,
    well_swapping_initial_state: Dict[Case, State],
) -> StateProcessor:
    return StateProcessor(
        well_swapping_state_machine,
        well_swapping_initial_state,
    )
