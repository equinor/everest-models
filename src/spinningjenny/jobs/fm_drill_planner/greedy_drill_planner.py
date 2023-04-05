import logging
from itertools import product

from spinningjenny.jobs.fm_drill_planner.utils import (
    Event,
    combine_slot_rig_unavailability,
    get_unavailability,
    valid_drill_combination,
)

logger = logging.getLogger(__name__)


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
                [name for name, slot in slots.items() if well in slot["wells"]]
                for well in wells
            ],
        )
    ):
        logger.info(
            f'wells {", ".join(wells.keys())} were unable to be drilled due to constraints'
        )

    return next_event


def _valid_events(wells, slots, rigs, horizon):
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
        if valid_drill_combination(well_name, slot_name, slot, rig)
        and (
            valid_time_box := _first_valid_timebox(
                well["drill_time"],
                rig["delay"],
                horizon,
                combine_slot_rig_unavailability(get_unavailability(horizon, slot, rig)),
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
                    -wells[event.well]["priority"],
                    -min(len(slots) for slots in well_slots if event.slot in slots),
                    event.begin,
                ),
            )
        ),
        None,
    )


def _remove_event_from_config(event, wells, slots, rigs, **kwargs):
    wells.pop(event.well)
    slots.pop(event.slot)
    rigs[event.rig].get("unavailability", []).append([event.begin, event.end])


def get_greedy_drill_plan(schedule, wells, **config):
    """
    Recursive function that eventually returns a well order schedule.

    This function should:
    - Retrieve the next best event
    - Append it to the schedule process the event in its configuration.
    - Start the next iteration with updated config and schedule
    """
    if not wells:
        return schedule

    if event := _get_next_event(wells, **config):
        _remove_event_from_config(event, wells, **config)
        schedule.append(event)
    else:
        wells = {}

    return get_greedy_drill_plan(schedule, wells, **config)
