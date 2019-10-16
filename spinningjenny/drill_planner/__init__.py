import collections
import numpy as np
from functools import partial
from datetime import timedelta

from spinningjenny import DATE_FORMAT, customized_logger

ScheduleEvent = collections.namedtuple(
    "schedule_event", ("rig", "slot", "well", "start_date", "end_date")
)

logger = customized_logger.get_logger(__name__)

ScheduleElement = collections.namedtuple(
    "schedule_element", ("rig", "slot", "well", "begin", "end")
)


def date_to_int(date, snapshot):
    return (date - snapshot.start_date).days


def create_config_dictionary(snapshot):
    date2int = partial(date_to_int, snapshot=snapshot)
    config = {}
    config["start_date"] = snapshot.start_date
    config["end_date"] = snapshot.end_date
    config["horizon"] = (snapshot.end_date - snapshot.start_date).days
    config["wells"] = {
        well_dict.name: {"drill_time": well_dict.drill_time}
        for well_dict in snapshot.wells
    }
    config["slots"] = {
        slot_dict.name: {
            "unavailability": [
                [date2int(elem.start), date2int(elem.stop)]
                for elem in (slot_dict.unavailability or [])
            ],
            "wells": list(slot_dict.wells),
        }
        for slot_dict in snapshot.slots
    }
    config["rigs"] = {
        rig_dict.name: {
            "unavailability": [
                [date2int(elem.start), date2int(elem.stop)]
                for elem in (rig_dict.unavailability or [])
            ],
            "wells": list(rig_dict.wells),
            "slots": list(rig_dict.slots),
            "delay": rig_dict.delay or 0,
        }
        for rig_dict in snapshot.rigs
    }
    config["wells_priority"] = dict(snapshot.wells_priority)

    return config


def append_data(input_values, schedule):
    for well_cfg in input_values:
        well_from_schedule = {
            "date": date for (well, date) in schedule if well == well_cfg["name"]
        }
        date = well_from_schedule["date"].strftime(DATE_FORMAT)

        well_cfg["readydate"] = date
        well_cfg["ops"] = [{"opname": "open", "date": date}]

    return input_values


def combine_slot_rig_unavailability(config, slot, rig):
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
    unavailability = np.zeros(config["horizon"])
    start_date = config["start_date"]

    for (start, end) in config["slots"][slot]["unavailability"]:
        unavailability[start:end] = 1

    for (start, end) in config["rigs"][rig]["unavailability"]:
        unavailability[start:end] = 1

    diff_array = np.diff(unavailability, 1)
    start_days = np.where(diff_array == 1)[0] + 1
    end_days = np.where(diff_array == -1)[0] + 1
    if unavailability[0] == 1:
        start_days = np.insert(start_days, 0, 0)
    if unavailability[-1] == 1:
        end_days = np.append(end_days, unavailability.shape[0])

    combined_unavailability = [
        [int(start), int(end)] for (start, end) in zip(start_days, end_days)
    ]
    return combined_unavailability


def valid_drill_combination(config, well, slot, rig):
    well_rig_match = well in config["rigs"][rig]["wells"]
    well_slot_match = well in config["slots"][slot]["wells"]
    slot_rig_match = slot in config["rigs"][rig]["slots"]

    return well_rig_match and well_slot_match and slot_rig_match


def repr_task(task):
    return "Task(rig={}, slot={}, well={}, start={}, end={})".format(
        task.rig, task.slot, task.well, task.begin, task.end
    )


def resolve_priorities(schedule, config):
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
    wells_priority = {k: v for k, v in config.wells_priority}
    sorted_schedule = sorted(
        schedule, key=lambda x: wells_priority[x.well], reverse=True
    )

    modified_schedule = [sorted_schedule[0]]

    for idx, event in enumerate(sorted_schedule[1:]):
        if modified_schedule[idx].end <= event.end:
            modified_schedule.append(event)
        else:
            modified_schedule.append(event._replace(end=modified_schedule[idx].end))
            msg = (
                "Well {first} could be completed prior to well {second}, "
                "without affecting {second}. End date for {first} shifted "
                "to conform with priority"
            )
            logger.info(
                msg.format(first=event.well, second=modified_schedule[idx].well)
            )
    return modified_schedule
