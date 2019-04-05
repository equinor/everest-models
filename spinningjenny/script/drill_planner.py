#!/usr/bin/env python
import argparse
import os
import sys
import yaml
from operator import attrgetter

from spinningjenny import customized_logger
from spinningjenny.drill_planner_optimization import evaluate

logger = customized_logger.get_logger(__name__)


def _verify_priority(schedule, config):
    for task1 in schedule:
        for task2 in schedule:
            priority1 = config["wells_priority"][task1.well]
            priority2 = config["wells_priority"][task2.well]
            if task1.start_date > task2.start_date:
                assert priority1 <= priority2


def _verify_constraints(config, schedule):
    for task in schedule:
        assert task.start_date >= config["start_date"]
        assert task.end_date <= config["end_date"]

        assert task.well in config["wells_at_rig"][task.rig]
        assert task.well in config["wells_at_slot"][task.slot]
        assert task.slot in config["slots_at_rig"][task.rig]

        rig_overlaps = [
            True
            for start, end in config["rig_unavailability"][task.rig]
            if (task.start_date < end and task.end_date > end)
            or (task.end_date > start and task.start_date < start)
        ]
        assert not any(rig_overlaps)

        slot_overlaps = [
            True
            for start, end in config["slot_unavailability"][task.slot]
            if (task.start_date < end and task.end_date > end)
            or (task.end_date > start and task.start_date < start)
        ]
        assert not any(slot_overlaps)

        assert config["drill_time"][task.well] == (task.end_date - task.start_date).days

    # ensure rig drills only one well at a time
    for rig in config["rigs"]:
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


def _export_fmt(schedule):
    schedule_well_order = {
        well: end_date.strftime("%Y-%m-%d")
        for (_, well, _, start_date, end_date) in schedule
    }
    return schedule_well_order


def _write_result(filename, schedule):
    formatted = _export_fmt(schedule)

    with open(filename, "w") as outfile:
        yaml.dump(formatted, outfile, default_flow_style=False)


def scheduler_parser():
    description = """
    A module that given a well priority list and a set of constraints,
    creates a list of dates for each well to be completed.\n
    Any well may have multiple options as to where it can be drilled,
    both for different slots and rigs. The module will try to find the
    optimum event combinations that allows for the wells to be completed
    as quickly as possible, and at the same time make sure that the
    dates that are output will be a valid drill plan.

    """
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "--config-file", required=True, type=_valid_file, help="Configuration file"
    )
    parser.add_argument(
        "--time-limit",
        required=False,
        type=int,
        default=3600,
        help="Maximum time limit for the solver in seconds.\n"
        "If a solution has not been reached within this time, a greedy"
        "approach will be used instead",
    )
    parser.add_argument(
        "--output_file",
        required=True,
        type=str,
        help="Name of the outputfile. The format will be yaml.",
    )
    return parser


def main_entry_point():
    parser = scheduler_parser()
    args = parser.parse_args(sys.argv[1:])
    logger.info("Initializing schedule evaluation")

    with open(args.config_file, "r") as config_file:
        config = yaml.safe_load(config_file)

    schedule = evaluate(max_solver_time=args.time_limit, **config)
    _verify_constraints(config, schedule)

    _log_detailed_result(schedule)
    _write_result(schedule, args.output_file)


if __name__ == "__main__":
    main_entry_point()
