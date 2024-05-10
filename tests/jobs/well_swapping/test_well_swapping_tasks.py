from everest_models.jobs.fm_well_swapping.state_processor import StateProcessor
from everest_models.jobs.fm_well_swapping.tasks import determine_index_states


def test_determin_index_state(well_swapping_state_processor: StateProcessor) -> None:
    state_transitions = determine_index_states(
        (
            (("one", "two", "three"), "open"),
            (("three", "two", "one"), "open"),
            (("three", "one", "two"), "open"),
            (("two", "one", "three"), "open"),
        ),
        well_swapping_state_processor,
        iterations=2,
    )
    assert state_transitions
