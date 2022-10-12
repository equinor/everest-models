import logging
from itertools import product

from jobs.fm_drill_planner.utils import (
    ScheduleElement,
    combine_slot_rig_unavailability,
    valid_drill_combination,
)

logger = logging.getLogger(__name__)


def _get_next_event(config):
    """
    This function filters out the mechanically impossible events (given by constraints in config)
    Then the best event is chosen from the filtered events.
    """
    valid_events = _valid_events(config)

    next_event = _next_best_event(config, valid_events)
    if not next_event:
        uncompleted_wells = config["wells"].keys()
        logger.info(
            "wells {} were unable to be drilled due to constraints".format(
                ", ".join(uncompleted_wells)
            )
        )

    return next_event


def _valid_events(config):
    """
    Applies various constraints to return only valid events
    """
    for well, slot, rig in product(
        sorted(config["wells"].keys()),
        sorted(config["slots"].keys()),
        sorted(config["rigs"].keys()),
    ):
        if valid_drill_combination(config, well, slot, rig):
            valid_timebox = _first_valid_timebox(config, well, slot, rig)
            if valid_timebox:
                begin, end = valid_timebox
                yield ScheduleElement(rig, slot, well, begin, end)


def _first_valid_timebox(config, well, slot, rig):
    event_unavailability = combine_slot_rig_unavailability(config, slot, rig)
    drilling_time = config["wells"][well]["drill_time"]
    drill_delay = config["rigs"][rig]["delay"]
    available_start = drill_delay

    for begin, end in event_unavailability:
        if begin > config["horizon"]:
            break
        if available_start + drilling_time <= begin:
            return [available_start, available_start + drilling_time]
        else:
            available_start = end + drill_delay + 1
    if available_start + drilling_time <= config["horizon"]:
        return [available_start, available_start + drilling_time]
    return None


def _next_best_event(config, events):
    """
    Determines the "best" event to select based on some heuristics in order:
        - The well priority: highest first
        - The slot-well specificity: highest first
        - The event's starting date: lowest first
    """
    slots_for_wells = {
        well: [
            slot for slot in config["slots"] if well in config["slots"][slot]["wells"]
        ]
        for well in config["wells"]
    }

    def slot_well_specificity(slot):
        return min([len(slots) for slots in slots_for_wells.values() if slot in slots])

    sorted_events = sorted(
        events,
        key=lambda event: (
            -config["wells_priority"][event.well],
            -slot_well_specificity(event.slot),
            event.begin,
        ),
    )
    return next(iter(sorted_events), None)


def get_greedy_drill_plan(config, schedule):
    """
    Recursive function that eventually returns a well order schedule.

    This function should:
    - Retrieve the next best event
    - Append it to the schedule process the event in its configuration.
    - Start the next iteration with updated config and schedule
    """
    if not config["wells"]:
        return schedule

    event = _get_next_event(config)
    if event:
        config["wells"].pop(event.well)
        config["wells_priority"].pop(event.well)
        config["slots"].pop(event.slot)
        config["rigs"][event.rig]["unavailability"].append([event.begin, event.end])

        schedule.append(event)
    else:
        config["wells"] = {}

    return get_greedy_drill_plan(config, schedule)
