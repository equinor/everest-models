#!/usr/bin/env python
import logging

from everest_models.jobs.fm_select_wells import tasks
from everest_models.jobs.fm_select_wells.parser import build_argument_parser

logger = logging.getLogger(__name__)


def main_entry_point(args=None):
    args_parser = build_argument_parser()
    options = args_parser.parse_args(args)
    well_number = tasks.get_well_number(options, error_msgr=args_parser.error)

    if not any((well_number, options.max_date)):
        args_parser.error(
            "\nBoth `well number` and `-m/--max-date` values are missing.\n"
            "Please provide either/or both values"
        )
    if options.lint:
        args_parser.exit()

    tasks.select_wells(
        wells=options.input,
        max_date=options.max_date,
        number_of_wells=well_number,
    )

    logger.info(f"Writing results to {options.output}")
    options.input.json_dump(options.output)


if __name__ == "__main__":
    main_entry_point()
