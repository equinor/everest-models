#!/usr/bin/env python
import logging
from copy import deepcopy
from datetime import date, timedelta

import configsuite

from spinningjenny.jobs.fm_drill_planner import drill_planner_schema
from spinningjenny.jobs.fm_drill_planner.drillmodel import FieldManager, FieldSchedule
from spinningjenny.jobs.fm_drill_planner.greedy_drill_planner import (
    get_greedy_drill_plan,
)
from spinningjenny.jobs.fm_drill_planner.ormodel import run_optimization
from spinningjenny.jobs.fm_drill_planner.parser import args_parser
from spinningjenny.jobs.fm_drill_planner.utils import (
    add_missing_slots,
    append_data,
    create_config_dictionary,
    resolve_priorities,
)
from spinningjenny.jobs.shared.io_utils import write_json_to_file

logger = logging.getLogger(__name__)


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


def _prepare_config(config, optimizer_values, input_values):
    config["wells_priority"] = optimizer_values
    config["wells"] = input_values

    # By default, if there are no slots defined in the rig entry, add slots corresponding to wells.
    config = add_missing_slots(config)

    return configsuite.ConfigSuite(
        config,
        drill_planner_schema.build(),
        extract_validation_context=drill_planner_schema.extract_validation_context,
        deduce_required=True,
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
        greedy_schedule = get_greedy_drill_plan(deepcopy(config_dic), [])
        or_tools_schedule = run_optimization(
            field_manager,
            best_guess_schedule=greedy_schedule,
            max_solver_time=time_limit,
        )

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
    args = args_parser.parse_args(args)

    logger.info("Validating config file")

    if args.ignore_end_date and "end_date" in args.config:
        args.config["end_date"] = date(3000, 1, 1)

    config = _prepare_config(
        config=args.config, optimizer_values=args.optimizer, input_values=args.input
    )

    if not config.valid:
        args_parser.error(
            "Invalid config file: {}\n{}".format(
                args.config, "\n".join([err.msg for err in config.errors])
            )
        )

    logger.info("Initializing drill planner")
    schedule = _run_drill_planner(config=config, time_limit=args.time_limit)

    start_date = config.snapshot.start_date
    _log_detailed_result(schedule, start_date)

    schedule = {
        elem.well: {
            "completion_date": start_date + timedelta(days=elem.completion),
            "readydate": start_date + timedelta(days=elem.end),
        }
        for elem in schedule
    }

    result = append_data(input_values=args.input, schedule=schedule)
    write_json_to_file(result, args.output)


if __name__ == "__main__":
    main_entry_point()
