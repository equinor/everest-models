import numpy as np
from spinningjenny import DATE_FORMAT
from datetime import timedelta
from operator import attrgetter


def create_config_dictionary(snapshot):
    config = {}
    config["start_date"] = snapshot.start_date
    config["end_date"] = snapshot.end_date
    config["wells"] = {
        well_dict.name: {"drill_time": well_dict.drill_time}
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


def append_data(input_values, schedule):
    for well_cfg in input_values:
        well_from_schedule = {
            "end_date": end_date
            for (_, _, well, _, end_date) in schedule
            if well == well_cfg["name"]
        }
        date = well_from_schedule["end_date"].strftime(DATE_FORMAT)

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
    unavailability = np.zeros((config["end_date"] - config["start_date"]).days)
    start_date = config["start_date"]

    for (start, end) in config["slots"][slot]["unavailability"]:
        start_int = (start - start_date).days
        end_int = (end - start_date).days
        unavailability[start_int:end_int] = 1

    for (start, end) in config["rigs"][rig]["unavailability"]:
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


def valid_drill_combination(config, well, slot, rig):
    well_rig_match = well in config["rigs"][rig]["wells"]
    well_slot_match = well in config["slots"][slot]["wells"]
    slot_rig_match = slot in config["rigs"][rig]["slots"]

    return well_rig_match and well_slot_match and slot_rig_match


def repr_task(task):
    return "Task(rig={}, slot={}, well={}, start={}, end={})".format(
        task.rig,
        task.slot,
        task.well,
        task.start_date.strftime(DATE_FORMAT),
        task.end_date.strftime(DATE_FORMAT),
    )


def verify_constraints(config, schedule):
    errors = []
    drilled_wells = []
    for task in schedule:
        if task.start_date < config["start_date"]:
            errors.append("{} starts before config start date.".format(repr_task(task)))
        if task.end_date > config["end_date"]:
            errors.append("{} ends after config end date.".format(repr_task(task)))

        if not valid_drill_combination(config, task.well, task.slot, task.rig):
            errors.append(
                "{} represents an invalid drill combination".format(repr_task(task))
            )

        combined_unavailability = combine_slot_rig_unavailability(
            config, task.slot, task.rig
        )
        overlaps = [
            task.start_date < period_end and task.end_date > period_start
            for period_start, period_end in combined_unavailability
        ]
        if any(overlaps):
            msg = "Rig {} or Slot {} is unavailable during {}.".format(
                task.rig, task.slot, repr_task(task)
            )
            errors.append(msg)

        drilling_time = config["wells"][task.well]["drill_time"]
        if not drilling_time == (task.end_date - task.start_date).days:
            msg = "Well {}'s drilling time does not line up with that of {}.".format(
                task.well, repr_task(task)
            )
            errors.append(msg)
        if task.well in drilled_wells:
            errors.append("Well {} was already drilled".format(task.well))
        else:
            drilled_wells.append(task.well)

    # ensure rig drills only one well at a time
    for rig in config["rigs"]:
        sorted_tasks = sorted(
            [task for task in schedule if task.rig == rig], key=attrgetter("start_date")
        )
        successive_tasks = zip(sorted_tasks[:-1], sorted_tasks[1:])
        for task1, task2 in successive_tasks:
            if task1.end_date > task2.start_date:
                errors.append(
                    "{} ends after {} begins.".format(
                        repr_task(task1), repr_task(task2)
                    )
                )

    # ensure each slot is only drilled once
    slots_in_schedule = [task.slot for task in schedule]
    if not len(set(slots_in_schedule)) == len(slots_in_schedule):
        errors.append("A slot is drilled through multiple times.")

    return errors
