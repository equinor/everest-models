#!/usr/bin/env python
import logging

from spinningjenny.jobs.fm_select_wells import tasks
from spinningjenny.jobs.fm_select_wells.parser import args_parser
from spinningjenny.jobs.shared.io_utils import write_json_to_file

logger = logging.getLogger(__name__)


def main_entry_point(args=None):
    args = args_parser.parse_args(args)

    well_number = None
    if args.well_number_file is not None:
        if args.real_bounds is None or args.scaled_bounds is None:
            args_parser.error(
                "Scaling bounds must be provided if -f/--well-number-file is given"
            )
        well_number = next(iter(args.well_number_file.values()))

    if args.well_number is not None:
        if not (args.real_bounds is None and args.scaled_bounds is None):
            args_parser.error(
                "Scaling bounds are not allowed if -n/--well-number is given"
            )
        well_number = args.well_number
        if well_number < 1:
            args_parser.error("-n/--well-number must be > 0")

    if (
        args.well_number_file is None
        and args.well_number is None
        and args.max_date is None
    ):
        args_parser.error(
            "-n/--well-number and -f/--well-number-file are both missing:"
            " -m/--max-date is required"
        )

    output = tasks.select_wells(
        args.input, well_number, args.real_bounds, args.scaled_bounds, args.max_date
    )

    logger.info(f"Writing results to {args.output}")
    write_json_to_file(output, args.output)


if __name__ == "__main__":
    main_entry_point()
