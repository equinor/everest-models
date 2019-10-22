#!/usr/bin/env python
import argparse
import configsuite

from copy import deepcopy
from datetime import timedelta
from functools import partial

from spinningjenny import customized_logger, valid_yaml_file, write_json_to_file
from spinningjenny.drill_planner.drillmodel import FieldManager, FieldSchedule
from spinningjenny.drill_planner.ormodel import run_optimization
from spinningjenny.drill_planner import (
    drill_planner_schema,
    create_config_dictionary,
    append_data,
    resolve_priorities,
)
from spinningjenny.drill_planner.greedy_drill_planner import get_greedy_drill_plan

logger = customized_logger.get_logger(__name__)


def _log_detailed_result(schedule, start_date):
    logger.info("Scheduler result:")
    for task in schedule:
        msg = (
            "Well {} is drilled at rig {} through slot {}, "
            "starting on date: {}, completed on date: {}"
        )
        logger.info(
            msg.format(
                task.well,
                task.rig,
                task.slot,
                start_date + timedelta(task.begin),
                start_date + timedelta(task.end),
            )
        )


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


def _compare_schedules(or_schedule, greedy_schedule, wells_priority):
    if not (or_schedule and greedy_schedule):
        return or_schedule or greedy_schedule

    if len(or_schedule) != len(greedy_schedule):
        return max([or_schedule, greedy_schedule])

    sorted_or_schedule = sorted(
        or_schedule, key=lambda element: wells_priority[element.well], reverse=True
    )
    sorted_greedy_schedule = sorted(
        greedy_schedule, key=lambda element: wells_priority[element.well], reverse=True
    )

    for or_element, greedy_element in zip(sorted_or_schedule, sorted_greedy_schedule):
        if or_element.end < greedy_element.end:
            return or_schedule
        if greedy_element.end < or_element.end:
            return greedy_schedule
    return or_schedule


def _run_drill_planner(config, time_limit):
    config_dic = create_config_dictionary(config.snapshot)
    drill_delays = [rig["delay"] for rig in config_dic["rigs"].values()]
    field_manager = FieldManager.generate_from_snapshot(config.snapshot)

    if any(drill_delays):
        schedule = get_greedy_drill_plan(deepcopy(config_dic), [])
    else:
        or_tools_schedule = run_optimization(field_manager, max_solver_time=time_limit)
        greedy_schedule = get_greedy_drill_plan(deepcopy(config_dic), [])

        schedule = _compare_schedules(
            or_tools_schedule, greedy_schedule, config_dic["wells_priority"]
        )

    field_schedule = FieldSchedule(schedule)
    if not field_manager.valid_schedule(field_schedule):

        raise RuntimeError(
            "Schedule created was not valid according to the constraints"
        )

    schedule = resolve_priorities(field_schedule.elements, config.snapshot)
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

    start_date = config.snapshot.start_date
    _log_detailed_result(schedule, start_date)

    schedule = [(elem.well, start_date + timedelta(days=elem.end)) for elem in schedule]

    result = append_data(input_values=args.input, schedule=schedule)
    write_json_to_file(result, args.output)


if __name__ == "__main__":
    main_entry_point()
