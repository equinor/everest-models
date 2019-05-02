#!/usr/bin/env python
import argparse
import sys
import os
from spinningjenny.strip_dates_job import strip_dates, process_dates
from spinningjenny import customized_logger, str2date

logger = customized_logger.get_logger(__name__)


def _build_argument_parser():
    description = (
        "The strip_dates job makes sure the summary file contains only report"
        " steps at the dates specified in the dates file"
    )
    parser = argparse.ArgumentParser(description=description)

    parser.add_argument("--summary", required=True, help="Ecl summary file")

    parser.add_argument(
        "--dates",
        nargs="*",  # 0 or more values expected => creates a list
        type=lambda d: str2date(d),
        required=True,
        help="List of date to remain in the summary file",
    )

    return parser


def main_entry_point():
    arg_parser = _build_argument_parser()
    args, _ = arg_parser.parse_known_args(sys.argv[1:])

    if os.path.exists(args.summary):
        strip_dates(summary_file=args.summary, dates=process_dates(args.dates))
    else:
        logger.error("No such file or directory: {}".format(args.summary))


if __name__ == "__main__":
    main_entry_point()
