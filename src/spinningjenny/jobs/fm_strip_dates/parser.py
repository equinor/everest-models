import argparse
import datetime
from functools import partial

from spinningjenny.jobs.utils.validators import valid_file


def build_argument_parser():
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
        type=lambda d: datetime.date.fromisoformat(d),
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


args_parser = build_argument_parser()
