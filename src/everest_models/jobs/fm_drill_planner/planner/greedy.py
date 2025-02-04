import copy
import itertools
import logging
from itertools import product
from typing import TYPE_CHECKING, Dict, List

import numpy as np

from everest_models.jobs.fm_drill_planner.data import Event, Rig, Slot, WellPriority

if TYPE_CHECKING:
    import numpy.typing as npt

logger = logging.getLogger(__name__)


def _combine_slot_rig_unavailability(unavailability):
    """
    This function combines an event's slot and rig unavailability's
    into a combined unavailability list for the event.

    Given the following scenario:
    rigs:
    -
        name: 'A'
        unavailability:
        -
            start: 2000-01-01
            stop: 2000-02-02
        -
            start: 2000-03-14
            stop: 2000-03-19
    slots:
    -
        name: 'S1'
        unavailability:
        -
            start: 2000-03-08
            stop: 2000-03-16

    This function would return the following result:
    [(2000-01-01, 2000-02-02), (2000-03-08, 2000-03-19)]
    """
    diff_array = np.diff(unavailability, 1)
    start_days = np.where(diff_array == 1)[0] + 1
    end_days = np.where(diff_array == -1)[0] + 1

    return zip(
        np.insert(start_days, 0, 0) if unavailability[0] else start_days,
        np.append(end_days, unavailability.shape[0])
        if unavailability[-1]
        else end_days,
    )


def _get_unavailability(horizon: int, slot: Slot, rig: Rig) -> "npt.NDArray[np.int8]":
    unavailability = np.zeros(horizon, dtype=np.int8)

    for day_range in itertools.chain(slot.day_ranges, rig.day_ranges):
        unavailability[day_range.begin : day_range.end] = 1
    return unavailability


def _valid_drill_combination(well_name: str, slot_name: str, slot: Slot, rig: Rig):
    return well_name in rig.wells and well_name in slot.wells and slot_name in rig.slots


def _get_next_event(wells, slots, rigs, horizon, **kwargs):
    """
    This function filters out the mechanically impossible events (given by constraints in config)
    Then the best event is chosen from the filtered events.
    """

    if not (
        next_event := _next_best_event(
            _valid_events(wells, slots, rigs, horizon),
            wells,
            well_slots=[
                [name for name, slot in slots.items() if well in slot.wells]
                for well in wells
            ],
        )
    ):
        logger.info(
            f"wells {', '.join(wells.keys())} were unable to be drilled due to constraints"
        )

    return next_event


def _valid_events(
    wells: Dict[str, WellPriority],
    slots: Dict[str, Slot],
    rigs: Dict[str, Rig],
    horizon: int,
) -> List[Event]:
    """
    Applies various constraints to return only valid events
    """
    return [
        Event(rig_name, slot_name, well_name, *valid_time_box)
        for (well_name, well), (slot_name, slot), (rig_name, rig) in product(
            sorted(wells.items()),
            sorted(slots.items()),
            sorted(rigs.items()),
        )
        if _valid_drill_combination(well_name, slot_name, slot, rig)
        and (
            valid_time_box := _first_valid_timebox(
                well.drill_time,
                rig.delay,
                horizon,
                _combine_slot_rig_unavailability(
                    _get_unavailability(horizon, slot, rig)
                ),
            )
        )
    ]


def _first_valid_timebox(drilling_time, drill_delay, horizon, unavailability):
    def get_available_start(begin, end, available=drill_delay):
        if begin is None or begin > horizon or available + drilling_time <= begin:
            return available
        return get_available_start(
            *next(unavailability, (None, None)), end + drill_delay + 1
        )

    if (
        available_start := get_available_start(*next(unavailability, (None, None)))
    ) + drilling_time <= horizon:
        return available_start, available_start + drilling_time


def _next_best_event(events, wells, well_slots):
    """
    Determines the "best" event to select based on some heuristics in order:
        - The well priority: highest first
        - The slot-well specificity: highest first
        - The event's starting date: lowest first
    """
    return next(
        iter(
            sorted(
                events,
                key=lambda event: (
                    -wells[event.well].priority,
                    -min(len(slots) for slots in well_slots if event.slot in slots),
                    event.begin,
                ),
            )
        ),
        None,
    )


def _remove_event_from_config(
    event,
    wells: Dict[str, WellPriority],
    slots: Dict[str, Slot],
    rigs: Dict[str, Rig],
    **kwargs,
):
    wells.pop(event.well)
    slots.pop(event.slot)
    rigs[event.rig].append_day_range(event.begin, event.end)


def _get_greedy_drill_plan(schedule, wells, **config) -> List[Event]:
    if not wells:
        return schedule

    if event := _get_next_event(wells, **config):
        _remove_event_from_config(event, wells, **config)
        schedule.append(event)
    else:
        wells = {}

    return _get_greedy_drill_plan(schedule, wells, **config)


def get_greedy_drill_plan(
    wells: Dict[str, WellPriority],
    slots: Dict[str, Slot],
    rigs: Dict[str, Rig],
    horizon: int,
) -> List[Event]:
    """Recursively build a well order schedule with parameters' copy.

    if wells is empty return schedule
    if next event is None: set wells to empty

    This function should:
    - Retrieve the next best greedy event
    - Append Event to the schedule
    - Start the next updated config iteration

    Args:
        wells (Dict[str, WellPriority]): well's drill time and priority
        slots (Dict[str, Slot]): all rigs' slots
        rigs (Dict[str, Rig]): rigs metadata
        horizon (int): date period

    Returns:
        List[Event]: a greedy rendition of event schedule
    """
    return _get_greedy_drill_plan(
        [],
        wells=copy.deepcopy(wells),
        slots=copy.deepcopy(slots),
        rigs=copy.deepcopy(rigs),
        horizon=horizon,
    )
