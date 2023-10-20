#!/usr/bin/env python

import datetime

from everest_models.jobs.fm_drill_planner.manager import get_field_manager
from everest_models.jobs.fm_drill_planner.parser import build_argument_parser
from everest_models.jobs.shared.models.wells import Operation


def main_entry_point(args=None):
    args_parser = build_argument_parser()
    options = args_parser.parse_args(args)

    manager = get_field_manager(
        options.config,
        options.input,
        options.optimizer,
        options.ignore_end_date,
        options.lint,
    )

    if options.lint:
        args_parser.exit()

    manager.run_schedule_optimization(options.time_limit)
    date = lambda days: options.config.start_date + datetime.timedelta(days=int(days))
    wells = options.input.to_dict()
    for event in manager.schedule():
        if well := wells[event.well]:
            ready_date = date(days=event.end)
            well.readydate = ready_date
            well.completion_date = date(days=event.completion)
            well.ops = (Operation.parse_obj({"opname": "open", "date": ready_date}),)

    options.input.json_dump(options.output)


if __name__ == "__main__":
    main_entry_point()
