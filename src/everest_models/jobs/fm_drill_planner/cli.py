#!/usr/bin/env python

from everest_models.jobs.fm_drill_planner.manager import get_field_manager
from everest_models.jobs.fm_drill_planner.parser import build_argument_parser
from everest_models.jobs.fm_drill_planner.tasks import orcastrate_drill_schedule


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
    orcastrate_drill_schedule(
        manager, options.input.to_dict(), options.config.start_date, options.time_limit
    )
    options.input.json_dump(options.output)


if __name__ == "__main__":
    main_entry_point()
