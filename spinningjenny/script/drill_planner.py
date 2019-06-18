#!/usr/bin/env python
import argparse
import os
import sys
import yaml
from operator import attrgetter
import configsuite
import json

from spinningjenny import customized_logger
from spinningjenny.drill_planner.drill_planner_optimization import evaluate
from spinningjenny.drill_planner import drill_planner_schema

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
    return (start_one < end_two and end_one > end_two) or (
        end_one > start_two and start_one < start_two
    )


def _verify_constraints(config, schedule):
    wells_at_rig = {rig.name: rig.wells for rig in config.rigs}
    wells_at_slot = {slot.name: slot.wells for slot in config.slots}
    slots_at_rig = {rig.name: rig.slots for rig in config.rigs}
    rig_unavailability = {rig.name: rig.unavailability for rig in config.rigs}
    slot_unavailability = {slot.name: slot.unavailability for slot in config.slots}
    drill_time = {well.name: well.drilltime for well in config.wells}

    for task in schedule:
        assert task.start_date >= config.start_date
        assert task.end_date <= config.end_date

        assert task.well in wells_at_rig[task.rig]
        assert task.well in wells_at_slot[task.slot]
        assert task.slot in slots_at_rig[task.rig]

        ranges = rig_unavailability[task.rig]
        if ranges:
            rig_overlaps = [
                _overlaps((task.start_date, task.end_date), (period.start, period.stop))
                for period in ranges
            ]
            assert not any(rig_overlaps)

        ranges = slot_unavailability[task.slot]
        if ranges:
            slot_overlaps = [
                _overlaps((task.start_date, task.end_date), (period.start, period.stop))
                for period in ranges
            ]
            assert not any(slot_overlaps)

        assert drill_time[task.well] == (task.end_date - task.start_date).days

    # ensure rig drills only one well at a time
    for rig in [rig.name for rig in config.rigs]:
        rig_tasks = [task for task in schedule if task.rig == rig]
        sorted_tasks = sorted(rig_tasks, key=attrgetter("start_date"))
        succesive_tasks = [
            (sorted_tasks[i], sorted_tasks[i + 1]) for i in range(len(sorted_tasks) - 1)
        ]
        for task1, task2 in succesive_tasks:
            assert task1.end_date <= task2.start_date


def _valid_file(fname):
    if not os.path.isfile(fname):
        raise AttributeError("File was not found: {}".format(fname))
    return fname


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


def _append_data(input_file, schedule):
    with open(input_file, "r") as input_file:
        input_values = yaml.safe_load(input_file)

    for well_cfg in input_values:
        well_from_schedule = {
            "end_date": end_date
            for (_, _, well, _, end_date) in schedule
            if well == well_cfg["name"]
        }
        date = well_from_schedule["end_date"].strftime("%Y-%m-%d")

        well_cfg["readydate"] = date
        well_cfg["ops"] = [{"opname": "open", "date": date}]

    return input_values


def _write_result(filename, data):
    with open(filename, "w") as outfile:
        json.dump(data, outfile, indent=4, separators=(",", ": "))


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
        "--input-file",
        required=True,
        type=_valid_file,
        help="File containing information related to wells. The format is "
        "consistent with the wells.json file when running everest and can "
        "be used directly.",
    )
    parser.add_argument(
        "--config-file",
        required=True,
        type=_valid_file,
        help="Configuration file describing the constraints of the field "
        "development. The file must contain information about rigs and slots "
        "that the wells can be drilled through. Additional information, such as "
        "when rigs and slots are available is also added here.",
    )
    parser.add_argument(
        "--optimizer-file",
        required=True,
        type=_valid_file,
        help="The optimizer file is the file output from everest that contains "
        "the well priority values - a float for each well.",
    )
    parser.add_argument(
        "--time-limit",
        required=False,
        type=int,
        default=3600,
        help="Maximum time limit for the solver in seconds."
        "If a solution has not been reached within this time, a greedy"
        "approach will be used instead.",
    )
    parser.add_argument(
        "--output-file",
        required=True,
        type=str,
        help="Name of the output-file. The output-file will contain the same "
        "information as the input-file, including the results from the "
        "drill_planner. Please note that it is highly recommended to not use the "
        "same filename as the input-file. In cases where the same workflow is run "
        "twice, it is generally adviced that the input-file for each job is consistent",
    )
    return parser


def _prepare_config(config_file, optimizer_file, input_file):
    with open(config_file, "r") as config_file:
        config = yaml.safe_load(config_file)

    with open(optimizer_file, "r") as optimizer_file:
        optimizer_values = yaml.safe_load(optimizer_file)

    with open(input_file, "r") as input_file:
        input_values = yaml.safe_load(input_file)

    config["wells_priority"] = optimizer_values
    config["wells"] = input_values

    return configsuite.ConfigSuite(
        config,
        drill_planner_schema.build(),
        extract_validation_context=drill_planner_schema.extract_validation_context,
    )


def _run_drill_planner(config, time_limit):
    schedule = evaluate(config.snapshot, max_solver_time=time_limit)
    _verify_constraints(config.snapshot, schedule)
    return schedule


def main_entry_point(args=None):

    if args is None:
        args = sys.argv[1:]

    parser = scheduler_parser()
    args = parser.parse_args(args)

    logger.info("Validating config file")

    config = _prepare_config(
        config_file=args.config_file,
        optimizer_file=args.optimizer_file,
        input_file=args.input_file,
    )

    if not config.valid:
        logger.error(
            "The configuration did not pass validation. Please review the errors:"
        )
        for error in config.errors:
            logger.error(error)
        sys.exit(1)

    logger.info("Initializing drill planner")
    schedule = _run_drill_planner(config=config, time_limit=args.time_limit)
    result = _append_data(input_file=args.input_file, schedule=schedule)

    _log_detailed_result(schedule)
    _write_result(filename=args.output_file, data=result)


if __name__ == "__main__":
    main_entry_point()
