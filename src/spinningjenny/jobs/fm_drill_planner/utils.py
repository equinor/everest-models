import itertools
import logging
from typing import Iterable

import numpy as np

logger = logging.getLogger(__name__)


class Event:
    def __init__(self, rig, slot, well, begin, end):
        self.rig = rig
        self.slot = slot
        self.well = well
        self.begin = begin
        self.end = end
        self.completion = end


def date_to_int(date, snapshot):
    return (date - snapshot.start_date).days


def create_config_dictionary(snapshot):
    def get_unavailability(unavailability):
        return [
            tuple((date - snapshot.start_date).days for date in unavailable)
            for unavailable in unavailability
        ]

    well_priority = dict(snapshot.wells_priority)
    return {
        "start_date": snapshot.start_date,
        "end_date": snapshot.end_date,
        "horizon": (snapshot.end_date - snapshot.start_date).days,
        "wells_priority": well_priority,
        "wells": {
            well.name: {
                "drill_time": well.drill_time,
                "priority": well_priority[well.name],
            }
            for well in snapshot.wells
        },
        "slots": {
            slot.name: {
                "unavailability": get_unavailability(slot.unavailability or []),
                "wells": list(slot.wells),
            }
            for slot in snapshot.slots
        },
        "rigs": {
            rig.name: {
                "unavailability": get_unavailability(rig.unavailability or []),
                "wells": list(rig.wells),
                "slots": list(rig.slots),
                "delay": rig.delay or 0,
            }
            for rig in snapshot.rigs
        },
    }


def append_data(input_values, schedule):
    for well_cfg in input_values:
        if scheduled_well := schedule.get(well_cfg["name"]):
            ready_date = str(scheduled_well["readydate"])
            well_cfg["readydate"] = ready_date
            well_cfg["completion_date"] = str(scheduled_well["completion_date"])
            well_cfg["ops"] = [{"opname": "open", "date": ready_date}]

    return input_values


def get_unavailability(horizon, slot, rig):
    unavailability = np.zeros(horizon, dtype=np.int8)

    for start, end in itertools.chain(slot["unavailability"], rig["unavailability"]):
        unavailability[start:end] = 1
    return unavailability


def combine_slot_rig_unavailability(unavailability):
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


def valid_drill_combination(well_name, slot_name, slot, rig):
    well_rig_match = well_name in rig["wells"]
    well_slot_match = well_name in slot["wells"]
    slot_rig_match = slot_name in rig["slots"]

    return well_rig_match and well_slot_match and slot_rig_match


def repr_task(task):
    return (
        f"Task(rig={task.rig}, slot={task.slot}, well={task.well}, "
        f"start={task.begin}, end={task.end})"
    )


def pairwise(iterable):
    # pairwise('ABCDEFG') --> AB BC CD DE EF FG
    a, b = itertools.tee(iterable)
    next(b, None)
    return zip(a, b)


def resolve_priorities(schedule: Iterable[Event], config):
    """
    The priorities are not hard constraints in the solvers, which they shouldn't be.
    Both implementations should prioritize the higher priority wells first.
    If, and only if, higher priority wells are not affected, a lower priority well
    can be drilled first. Otherwise forcing the startup for lower priority wells
    could result in wells not beeing drilled.

    The output of the entire job however should not allow for ready_dates to be
    in any other order than as a prioritized list. We therefore shift any
    dates that are not in order.
    """

    def priority(previous, current):
        if previous.end > current.end:
            current.end = previous.end
            logger.info(
                f"Well {current.well} could be completed prior to well {previous.well}, "
                f"without affecting {previous.well}. End date for {current.well} shifted "
                "to conform with priority"
            )
        return current

    sorted_schedule = sorted(
        schedule, key=lambda x: dict(config.wells_priority)[x.well], reverse=True
    )

    return [
        sorted_schedule[0],
        *[priority(prev, curr) for prev, curr in pairwise(sorted_schedule)],
    ]


def _unique_slot_names(rig_name, slot_names):
    """Generate unique slot names based on the rig name and an index."""
    inx = 0
    while True:
        if (slot := f"_{rig_name}_slot_{inx}") not in slot_names:
            yield slot
        inx = inx + 1


def _add_slots_to_rig(rig, slot_names):
    # Iterate over the wells, even when not using them, to get the slot count right.
    return {
        slot_name: wells
        for wells, slot_name in zip(
            rig.get("wells", []), _unique_slot_names(rig["name"], slot_names)
        )
    }


def add_missing_slots(config):
    """
    In the configuration, slots can be defined in each rig entry. In simple,
    often used, cases there is a single slot for each well. In that case,
    defining all slots is cumbersome. This function can be called to add slots
    to the configuration dicts that is the input of ConfigSuite. In case the
    "slots" field is missing from a rig, it will add a slot for each well, and
    add them to the slots entry.
    """

    config.setdefault("slots", [])

    # Add slots to rigs that do not have them.result
    slot_names = {slot["name"] for slot in config["slots"]}

    def set_new_slots(rig):
        slots = _add_slots_to_rig(rig, slot_names)
        rig["slots"] = list(slots)
        return slots

    # Add slots that were added to the rigs above.
    config["slots"].extend(
        [
            {"name": slot, "wells": [well]}
            for rig in (
                set_new_slots(rig) for rig in config["rigs"] if "slots" not in rig
            )
            for slot, well in rig.items()
        ]
    )
