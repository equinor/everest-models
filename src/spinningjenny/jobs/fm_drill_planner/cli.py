#!/usr/bin/env python
import logging
from copy import deepcopy
from datetime import date, timedelta

import configsuite

from spinningjenny.jobs.fm_drill_planner import drill_planner_schema
from spinningjenny.jobs.fm_drill_planner.drillmodel import FieldManager
from spinningjenny.jobs.fm_drill_planner.greedy_drill_planner import (
    get_greedy_drill_plan,
)
from spinningjenny.jobs.fm_drill_planner.ormodel import (
    drill_constraint_model,
    run_optimization,
)
from spinningjenny.jobs.fm_drill_planner.parser import build_argument_parser
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
        logger.info(
            f"Well {task.well} is drilled at rig {task.rig} through slot {task.slot}, "
            f"starting on date: {start_date + timedelta(task.begin)}, "
            f"completed on date: {start_date + timedelta(task.end)}"
        )


def _prepare_config(config, optimizer_values, input_values):
    config["wells_priority"] = optimizer_values
    config["wells"] = input_values
    # By default, if there are no slots defined in the rig entry, add slots corresponding to wells.
    add_missing_slots(config)
    return configsuite.ConfigSuite(
        config,
        drill_planner_schema.build(),
        extract_validation_context=drill_planner_schema.extract_validation_context,
        deduce_required=True,
    )


def _compare_schedules(or_schedule, greedy_schedule, wells_priority):
    """given a greedy- and or-schedule pick one of the two"""

    # if one of the two of the schedule are not present return the other
    if not (or_schedule and greedy_schedule):
        return or_schedule or greedy_schedule

    # if length of the schedule are not the same return the max of the two
    if len(or_schedule) != len(greedy_schedule):
        return max([or_schedule, greedy_schedule])

    def sorted_schedule(schedule):
        return sorted(
            schedule,
            key=lambda element: wells_priority[element.well],
            reverse=True,
        )

    return next(
        (
            or_schedule if or_element.end < greedy_element.end else greedy_schedule
            for or_element, greedy_element in zip(
                sorted_schedule(or_schedule), sorted_schedule(greedy_schedule)
            )
            if or_element.end != greedy_element.end
        ),
        or_schedule,
    )


def _run_drill_planner(config, time_limit):
    config_dic = create_config_dictionary(config.snapshot)
    field_manager = FieldManager.generate_from_config(**config_dic)
    greedy_schedule = get_greedy_drill_plan([], **deepcopy(config_dic))
    field_schedule = (
        greedy_schedule
        if any(rig["delay"] for rig in config_dic["rigs"].values())
        else _compare_schedules(
            run_optimization(
                drill_constraint_model=drill_constraint_model(
                    field_manager.well_dict,
                    field_manager.slot_dict,
                    field_manager.rig_dict,
                    field_manager.horizon,
                    greedy_schedule,
                ),
                max_solver_time=time_limit,
            ),
            greedy_schedule,
            config_dic["wells_priority"],
        )
    )

    if not field_manager.valid_schedule(field_schedule):
        raise RuntimeError(
            "Schedule created was not valid according to the constraints"
        )

    return resolve_priorities(field_schedule, config.snapshot)


def main_entry_point(args=None):
    args_parser = build_argument_parser()
    options = args_parser.parse_args(args)

    logger.info("Validating config file")

    if options.ignore_end_date and "end_date" in options.config:
        options.config["end_date"] = date(3000, 1, 1)

    # for field, alias in (("optimizer", "well_priority"), ("input", "wells")):
    #     if (value := getattr(options, field, None)) is not None:
    #         setattr(options.config, alias or field, value)

    config = _prepare_config(
        config=options.config,
        optimizer_values=options.optimizer,
        input_values=options.input,
    )

    if not config.valid:
        args_parser.error(
            "Invalid config file: {}\n{}".format(
                options.config, "\n".join([err.msg for err in config.errors])
            )
        )

    logger.info("Initializing drill planner")
    schedule = _run_drill_planner(config=config, time_limit=options.time_limit)

    start_date = config.snapshot.start_date
    _log_detailed_result(schedule, start_date)

    schedule = {
        elem.well: {
            "completion_date": start_date + timedelta(days=elem.completion),
            "readydate": start_date + timedelta(days=elem.end),
        }
        for elem in schedule
    }

    result = append_data(input_values=options.input, schedule=schedule)
    write_json_to_file(result, options.output)


if __name__ == "__main__":
    main_entry_point()
