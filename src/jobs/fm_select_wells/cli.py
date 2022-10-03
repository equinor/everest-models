#!/usr/bin/env python
import argparse
import datetime
import logging
from functools import partial

from jobs.fm_select_wells import tasks
from jobs.utils.io_utils import write_json_to_file
from jobs.utils.validators import is_writable, valid_json_file

logger = logging.getLogger(__name__)


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Select the first wells from a drill planner output file."
    )
    well_number_group = parser.add_mutually_exclusive_group()
    parser.add_argument(
        "-i",
        "--input",
        required=True,
        type=partial(valid_json_file, parser=parser),
        help="Input file: a drill planner output file.",
    )
    well_number_group.add_argument(
        "-n",
        "--well-number",
        type=int,
        help="The number of wells.",
    )
    well_number_group.add_argument(
        "-f",
        "--well-number-file",
        type=partial(valid_json_file, parser=parser),
        help="Everest control file containing the number of wells.",
    )
    parser.add_argument(
        "-r",
        "--real-bounds",
        metavar=["LOWER", "UPPER"],
        type=int,
        help="Lower and upper bounds for the well number.",
        nargs=2,
    )
    parser.add_argument(
        "-s",
        "--scaled-bounds",
        metavar=["LOWER", "UPPER"],
        type=float,
        help="Scaled lower and upper bounds for the well number.",
        nargs=2,
    )
    parser.add_argument(
        "-m",
        "--max-date",
        type=datetime.date.fromisoformat,
        help="Maximum allowed date",
    )
    parser.add_argument(
        "-o",
        "--output",
        required=True,
        type=partial(is_writable, parser=parser),
        help="Output file: updated drill planner output file",
    )
    return parser


def main_entry_point(args=None):
    parser = parse_arguments()
    args = parser.parse_args(args)

    well_number = None
    if args.well_number_file is not None:
        if args.real_bounds is None or args.scaled_bounds is None:
            parser.error(
                "Scaling bounds must be provided if -f/--well-number-file is given"
            )
        well_number = next(iter(args.well_number_file.values()))

    if args.well_number is not None:
        if not (args.real_bounds is None and args.scaled_bounds is None):
            parser.error("Scaling bounds are not allowed if -n/--well-number is given")
        well_number = args.well_number
        if well_number < 1:
            parser.error("-n/--well-number must be > 0")

    if (
        args.well_number_file is None
        and args.well_number is None
        and args.max_date is None
    ):
        parser.error(
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
