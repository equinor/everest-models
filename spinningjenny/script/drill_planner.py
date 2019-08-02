#!/usr/bin/env python
import argparse
from operator import attrgetter
import configsuite
from functools import partial

from spinningjenny import (
    customized_logger,
    valid_yaml_file,
    write_json_to_file,
    DATE_FORMAT,
)
from spinningjenny.drill_planner.drill_planner_optimization import evaluate
from spinningjenny.drill_planner import drill_planner_schema
from spinningjenny.drill_planner.greedy_drill_planner import get_greedy_drill_plan
from copy import deepcopy

logger = customized_logger.get_logger(__name__)


def _verify_priority(schedule, config):
    for task1 in schedule:
        for task2 in schedule:
            priority1 = dict(config.wells_priority)[task1.well]
            priority2 = dict(config.wells_priority)[task2.well]
            if task1.start_date > task2.start_date:
                assert priority1 <= priority2


def _overlaps(range_one, range_two):
    start_one, end_one = range_one
    start_two, end_two = range_two
    return (end_one > start_two) and (start_one < end_two)


def _verify_constraints(config, schedule):
    errors = []

    wells_at_rig = {rig.name: rig.wells for rig in config.rigs}
    wells_at_slot = {slot.name: slot.wells for slot in config.slots}
    slots_at_rig = {rig.name: rig.slots for rig in config.rigs}
    rig_unavailability = {rig.name: rig.unavailability for rig in config.rigs}
    slot_unavailability = {slot.name: slot.unavailability for slot in config.slots}
    drill_time = {well.name: well.drill_time for well in config.wells}

    def repr_task(task):
        return "(rig={}, slot={}, well={}, start={}, end={})".format(
            task.rig,
            task.slot,
            task.well,
            task.start_date.strftime(DATE_FORMAT),
            task.end_date.strftime(DATE_FORMAT),
        )

    for task in schedule:
        if not task.start_date >= config.start_date:
            msg = "Task {} starts before config start date.".format(repr_task(task))
            logger.error(msg)
            errors.append(msg)
        if not task.end_date <= config.end_date:
            msg = "Task {} ends after config end date.".format(repr_task(task))
            logger.error(msg)
            errors.append(msg)

        if not task.well in wells_at_rig[task.rig]:
            msg = "Well {} cannot be drilled on rig {}.".format(task.well, task.rig)
            logger.error(msg)
            errors.append(msg)
        if not task.well in wells_at_slot[task.slot]:
            msg = "Well {} cannot be drilled through slot {}.".format(
                task.well, task.slot
            )
            logger.error(msg)
            errors.append(msg)
        if not task.slot in slots_at_rig[task.rig]:
            msg = "Slot {} cannot be drilled through with rig {}.".format(
                task.slot, task.rig
            )
            logger.error(msg)
            errors.append(msg)

        ranges = rig_unavailability[task.rig]
        if ranges:
            rig_overlaps = [
                _overlaps((task.start_date, task.end_date), (period.start, period.stop))
                for period in ranges
            ]
            if any(rig_overlaps):
                msg = "Rig {} is unavailable during task {}.".format(
                    task.rig, repr_task(task)
                )
                logger.error(msg)
                errors.append(msg)

        ranges = slot_unavailability[task.slot]
        if ranges:
            slot_overlaps = [
                _overlaps((task.start_date, task.end_date), (period.start, period.stop))
                for period in ranges
            ]
            if any(slot_overlaps):
                msg = "Slot {} is unavailable during task {}.".format(
                    task.slot, repr_task(task)
                )
                logger.error(msg)
                errors.append(msg)

        if not drill_time[task.well] == (task.end_date - task.start_date).days:
            msg = "Well {}'s drilling time does not line up with that of task {}.".format(
                task.well, repr_task(task)
            )
            logger.error(msg)
            errors.append(msg)

    # ensure rig drills only one well at a time
    for rig in [rig.name for rig in config.rigs]:
        rig_tasks = [task for task in schedule if task.rig == rig]
        sorted_tasks = sorted(rig_tasks, key=attrgetter("start_date"))
        succesive_tasks = [
            (sorted_tasks[i], sorted_tasks[i + 1]) for i in range(len(sorted_tasks) - 1)
        ]
        for task1, task2 in succesive_tasks:
            if not task1.end_date <= task2.start_date:
                msg = "Task {} ends after task {} begins.".format(
                    repr_task(task1), repr_task(task2)
                )
                logger.error(msg)
                errors.append(msg)

    # ensure each slot is only drilled once
    slots_in_schedule = [task.slot for task in schedule]
    if not len(set(slots_in_schedule)) == len(slots_in_schedule):
        msg = "A slot is drilled through multiple times."
        logger.error(msg)
        errors.append(msg)

    if errors:
        raise RuntimeError(errors)


def _log_detailed_result(schedule):
    logger.info("Scheduler result:")
    for task in schedule:
        msg = (
            "Well {} is drilled at rig {} through slot {}, "
            "starting on date: {}, completed on date: {}"
        )
        logger.info(
            msg.format(task.well, task.rig, task.slot, task.start_date, task.end_date)
        )


def _append_data(input_values, schedule):

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


def scheduler_parser():
    description = """
    A module that given a well priority list and a set of constraints,
    creates a list of dates for each well to be completed.
    Any well may have multiple options as to where it can be drilled,
    both for different slots and rigs. The module will try to find the
    optimum event combinations that allows for the wells to be completed
    as quickly as possible, and at the same time make sure that the
    dates that are output will be a valid drill plan.
    """
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "-i",
        "--input",
        required=True,
        type=partial(valid_yaml_file, parser=parser),
        help="File containing information related to wells. The format is "
        "consistent with the wells.json file when running everest and can "
        "be used directly.",
    )
    parser.add_argument(
        "-c",
        "--config",
        required=True,
        type=partial(valid_yaml_file, parser=parser),
        help="Configuration file describing the constraints of the field "
        "development. The file must contain information about rigs and slots "
        "that the wells can be drilled through. Additional information, such as "
        "when rigs and slots are available is also added here.",
    )
    parser.add_argument(
        "-opt",
        "--optimizer",
        required=True,
        type=partial(valid_yaml_file, parser=parser),
        help="The optimizer file is the file output from everest that contains "
        "the well priority values - a float for each well.",
    )
    parser.add_argument(
        "-tl",
        "--time-limit",
        required=False,
        type=int,
        default=3600,
        help="Maximum time limit for the solver in seconds."
        "If a solution has not been reached within this time, a greedy"
        "approach will be used instead.",
    )
    parser.add_argument(
        "-o",
        "--output",
        required=True,
        type=str,
        help="Name of the output-file. The output-file will contain the same "
        "information as the input-file, including the results from the "
        "drill_planner. Please note that it is highly recommended to not use the "
        "same filename as the input-file. In cases where the same workflow is run "
        "twice, it is generally adviced that the input-file for each job is consistent",
    )
    return parser


def _prepare_config(config, optimizer_values, input_values):
    config["wells_priority"] = optimizer_values
    config["wells"] = input_values

    return configsuite.ConfigSuite(
        config,
        drill_planner_schema.build(),
        extract_validation_context=drill_planner_schema.extract_validation_context,
    )


def _run_drill_planner(config, time_limit):
    schedule = evaluate(config.snapshot, max_solver_time=time_limit)
    if not schedule:
        logger.info(
            "Optimized drill plan was not found -    resolving using optimal localized decisions"
        )
        schedule = get_greedy_drill_plan(deepcopy(config))
    _verify_constraints(config.snapshot, schedule)
    return schedule


def main_entry_point(args=None):
    parser = scheduler_parser()
    args = parser.parse_args(args)

    logger.info("Validating config file")

    config = _prepare_config(
        config=args.config, optimizer_values=args.optimizer, input_values=args.input
    )

    if not config.valid:
        parser.error(
            "Invalid config file: {}\n{}".format(
                args.config, "\n".join([err.msg for err in config.errors])
            )
        )

    logger.info("Initializing drill planner")
    schedule = _run_drill_planner(config=config, time_limit=args.time_limit)
    result = _append_data(input_values=args.input, schedule=schedule)

    _log_detailed_result(schedule)
    write_json_to_file(result, args.output)


if __name__ == "__main__":
    main_entry_point()
