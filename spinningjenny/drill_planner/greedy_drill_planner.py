from itertools import product
from collections import namedtuple
from datetime import timedelta
import numpy as np
from spinningjenny.drill_planner.drill_planner_optimization import ScheduleEvent

event_tuple = namedtuple("Event", "well slot rig")


def get_drill_plan(config, schedule):
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
    drilling_timebox = _first_valid_timebox(config, event)

    config["wells"].pop(event.well)
    config["wells_priority"].pop(event.well)
    config["slots"].pop(event.slot)
    config["rigs"][event.rig]["unavailability"].append(drilling_timebox)

    schedule_event = ScheduleEvent(
        rig=event.rig,
        slot=event.slot,
        well=event.well,
        start_date=drilling_timebox[0],
        end_date=drilling_timebox[1],
    )

    schedule.append(schedule_event)

    return get_drill_plan(config, schedule)


def _get_next_event(config):
    """
    This function filters out the mechanically impossible events (given by constraints in config)
    Then the best event is chosen from the filtered events.
    """
    # Generate all possible events (rigs*slots*wells)
    all_events = [
        event_tuple(well=w, slot=s, rig=r)
        for w, s, r in product(
            sorted(config["wells"].keys()),
            sorted(config["slots"].keys()),
            sorted(config["rigs"].keys()),
        )
    ]

    valid_events = _filter_events(config, all_events)

    next_event = _next_best_event(config, valid_events)
    if not next_event:
        raise ValueError(
            "No valid event was found, there might be too many constraints."
        )
    return next_event


def _filter_events(config, events):
    """
    Applies various constraints to filter out invalid events
    """

    def valid_event(event):
        well_rig_match = event.well in config["rigs"][event.rig]["wells"]
        well_slot_match = event.well in config["slots"][event.slot]["wells"]
        slot_rig_match = event.slot in config["rigs"][event.rig]["slots"]

        valid_timebox = _first_valid_timebox(config, event)

        return well_rig_match and well_slot_match and slot_rig_match and valid_timebox

    return [event for event in events if valid_event(event)]


def _combine_slot_rig_unavailability(config, event):
    """
    This function combines an event's slot and rig unavailabilities
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
    unavailability = np.zeros((config["end_date"] - config["start_date"]).days)
    start_date = config["start_date"]

    for (start, end) in config["slots"][event.slot]["unavailability"]:
        start_int = (start - start_date).days
        end_int = (end - start_date).days
        unavailability[start_int:end_int] = 1

    for (start, end) in config["rigs"][event.rig]["unavailability"]:
        start_int = (start - start_date).days
        end_int = (end - start_date).days
        unavailability[start_int:end_int] = 1

    diff_array = np.diff(unavailability, 1)
    start_days = np.where(diff_array == 1)[0] + 1
    end_days = np.where(diff_array == -1)[0] + 1
    if unavailability[0] == 1:
        start_days = np.insert(start_days, 0, 0)
    if unavailability[-1] == 1:
        end_days = np.append(end_days, unavailability.shape[0])

    combined_unavailability = [
        [timedelta(days=int(start)) + start_date, timedelta(days=int(end)) + start_date]
        for (start, end) in zip(start_days, end_days)
    ]
    return combined_unavailability


def _first_valid_timebox(config, event):
    event_unavailability = _combine_slot_rig_unavailability(config, event)
    drilling_time = timedelta(days=config["wells"][event.well]["drilltime"])
    slot_start_available = config["start_date"]

    for start, end in event_unavailability:
        if start > config["end_date"]:
            break

        if slot_start_available + drilling_time <= start:
            return [slot_start_available, slot_start_available + drilling_time]
        else:
            slot_start_available = end + timedelta(days=1)
    if slot_start_available + drilling_time <= config["end_date"]:
        return [slot_start_available, slot_start_available + drilling_time]
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

    def starting_date(event):
        timebox = _first_valid_timebox(config, event)
        return timebox[0]

    sorted_events = sorted(
        events,
        key=lambda event: (
            -config["wells_priority"][event.well],
            -slot_well_specificity(event.slot),
            starting_date(event),
        ),
    )
    return sorted_events[0]


def create_config_dictionary(snapshot):
    config = {}
    config["start_date"] = snapshot.start_date
    config["end_date"] = snapshot.end_date
    config["wells"] = {
        well_dict.name: {"drilltime": well_dict.drilltime}
        for well_dict in snapshot.wells
    }
    config["slots"] = {
        slot_dict.name: {
            "unavailability": [
                [elem.start, elem.stop] for elem in (slot_dict.unavailability or [])
            ],
            "wells": list(slot_dict.wells),
        }
        for slot_dict in snapshot.slots
    }
    config["rigs"] = {
        rig_dict.name: {
            "unavailability": [
                [elem.start, elem.stop] for elem in (rig_dict.unavailability or [])
            ],
            "wells": list(rig_dict.wells),
            "slots": list(rig_dict.slots),
        }
        for rig_dict in snapshot.rigs
    }
    config["wells_priority"] = dict(snapshot.wells_priority)

    return config


def get_greedy_drill_plan(snapshot):
    config = create_config_dictionary(snapshot)
    schedule = get_drill_plan(config, [])
    return schedule
