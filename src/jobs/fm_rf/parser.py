import argparse
from functools import partial

from jobs.utils.validators import is_writable, valid_date, valid_ecl_file


def build_argument_parser():
    description = (
        "Calculates the recovery factor given summary keys and dates.\n"
        "Requires an EclSum instance to retrieve the volumes from. The summary "
        "keys requested must be in the EclSum instance. If the dates are outside "
        "the simulation range, they will be clamped to nearest. Will throw an "
        "error if the entire date range is outside the simulation range\n\n"
        "It is up to the caller to use sane combinations of summary keys."
    )
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "-s",
        "--summary",
        required=True,
        type=partial(valid_ecl_file, parser=parser),
        help="Eclipse summary file",
    )
    parser.add_argument(
        "-pk",
        "--production_key",
        default="FOPT",
        type=str,
        help="Production key - a valid summary key",
    )
    parser.add_argument(
        "-tvk",
        "--total_volume_key",
        default="FOIP",
        type=str,
        help="Total volume key - a valid summary key",
    )
    parser.add_argument(
        "-sd",
        "--start_date",
        default=None,
        type=partial(valid_date, parser=parser),
        help="Start date - As ISO8601 formatted date (YYYY-MM-DD)",
    )
    parser.add_argument(
        "-ed",
        "--end_date",
        default=None,
        type=partial(valid_date, parser=parser),
        help="Start date - As ISO8601 formatted date (YYYY-MM-DD)",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=partial(is_writable, parser=parser),
        required=False,
        help="Filename of the output file. ",
    )
    return parser


args_parser = build_argument_parser()
