from itertools import product
from datetime import timedelta
from spinningjenny.drill_planner import (
    combine_slot_rig_unavailability,
    valid_drill_combination,
)
from spinningjenny.drill_planner.drill_planner_optimization import ScheduleEvent
from spinningjenny import customized_logger

logger = customized_logger.get_logger(__name__)


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
                start_date, end_date = valid_timebox
                yield ScheduleEvent(rig, slot, well, start_date, end_date)


def _first_valid_timebox(config, well, slot, rig):
    event_unavailability = combine_slot_rig_unavailability(config, slot, rig)
    drilling_time = timedelta(days=config["wells"][well]["drill_time"])
    drill_delay = timedelta(days=config["rigs"][rig]["delay"])
    available_start_date = config["start_date"] + drill_delay

    for start, end in event_unavailability:
        if start > config["end_date"]:
            break

        if available_start_date + drilling_time <= start:
            return [available_start_date, available_start_date + drilling_time]
        else:
            available_start_date = end + drill_delay + timedelta(days=1)
    if available_start_date + drilling_time <= config["end_date"]:
        return [available_start_date, available_start_date + drilling_time]
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
            event.start_date,
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
        config["rigs"][event.rig]["unavailability"].append(
            [event.start_date, event.end_date]
        )

        schedule.append(event)
    else:
        config["wells"] = {}

    return get_greedy_drill_plan(config, schedule)
