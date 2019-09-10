#!/usr/bin/env python
import argparse
import configsuite

from functools import partial
from spinningjenny import customized_logger, valid_yaml_file, write_json_to_file
from spinningjenny.drill_planner.drill_planner_optimization import evaluate
from spinningjenny.drill_planner.drill_planner_schema import (
    extract_validation_context,
    config_schema,
)

from spinningjenny.drill_planner import (
    create_config_dictionary,
    append_data,
    verify_constraints,
)
from spinningjenny.drill_planner.greedy_drill_planner import get_greedy_drill_plan
from copy import deepcopy

logger = customized_logger.get_logger(__name__)


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


def _validate_config(file_path, parser, args):
    _parser = argparse.ArgumentParser()
    _parser.add_argument("-i", "--input", required=True)
    _parser.add_argument("-opt", "--optimizer", required=True)
    _parser.add_argument("-o", "--output", required=True)
    options, _ = _parser.parse_known_args(args)
    config = valid_yaml_file(file_path, parser)
    wells_priority = valid_yaml_file(options.optimizer, parser)
    wells = valid_yaml_file(options.input, parser)

    config["wells_priority"] = wells_priority
    config["wells"] = wells

    config = configsuite.ConfigSuite(
        config, config_schema(), extract_validation_context=extract_validation_context
    )
    if not config.valid:
        parser.error(
            "Invalid config file: {}\n{}".format(
                file_path, "\n".join([err.msg for err in config.errors])
            )
        )
    return config


def scheduler_parser(args=None):
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
        type=partial(_validate_config, parser=parser, args=args),
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


def _run_drill_planner(config, time_limit):
    config_dic = create_config_dictionary(config.snapshot)
    drill_delays = [rig["delay"] for rig in config_dic["rigs"].values()]

    if any(drill_delays):
        schedule = get_greedy_drill_plan(deepcopy(config_dic), [])
    else:
        schedule = evaluate(config.snapshot, max_solver_time=time_limit)
        if not schedule:
            logger.info(
                "Optimized drill plan was not found -    resolving using optimal localized decisions"
            )
            schedule = get_greedy_drill_plan(deepcopy(config_dic), [])
    error_msgs = verify_constraints(config_dic, schedule)
    if error_msgs:
        for err_msg in error_msgs:
            logger.error(err_msg)
        raise RuntimeError(error_msgs)

    return schedule


def main_entry_point(args=None):
    parser = scheduler_parser(args)
    args = parser.parse_args(args)

    logger.info("Initializing drill planner")
    schedule = _run_drill_planner(config=args.config, time_limit=args.time_limit)
    result = append_data(input_values=args.input, schedule=schedule)

    _log_detailed_result(schedule)
    write_json_to_file(result, args.output)


if __name__ == "__main__":
    main_entry_point()
