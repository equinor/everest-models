#!/usr/bin/env python
import argparse
import logging
import os
import sys
from functools import partial

from spinningjenny import str2date, valid_file
from spinningjenny.strip_dates_job import process_dates, strip_dates

logger = logging.getLogger(__name__)


def _build_argument_parser():
    description = (
        "Makes sure a given summary file contains only report steps at the "
        "list of dates given as an argument"
    )
    parser = argparse.ArgumentParser(description=description)

    parser.add_argument(
        "-s",
        "--summary",
        type=partial(valid_file, parser=parser),
        required=True,
        help="Ecl summary file",
    )

    parser.add_argument(
        "-d",
        "--dates",
        nargs="*",  # 0 or more values expected => creates a list
        type=lambda d: str2date(d),
        required=True,
        help="List of date to remain in the summary file",
    )

    parser.add_argument(
        "--allow-missing-dates",
        action="store_true",
        default=False,
        help="Do not fail if any requested dates are missing in the file",
    )

    return parser


def main_entry_point(args=None):
    arg_parser = _build_argument_parser()
    options = arg_parser.parse_args(args)

    if os.path.exists(options.summary):
        try:
            strip_dates(
                summary_file=options.summary,
                dates=process_dates(options.dates),
                allow_missing_dates=options.allow_missing_dates,
            )
        except RuntimeError as err:
            logger.error(str(err))
            sys.exit(1)
    else:
        logger.error("No such file or directory: {}".format(options.summary))


if __name__ == "__main__":
    main_entry_point()
