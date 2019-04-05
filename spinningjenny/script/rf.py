#!/usr/bin/env python
import argparse
import sys

from spinningjenny import customized_logger
from spinningjenny.rf_job import recovery_factor

logger = customized_logger.get_logger(__name__)


def rf_parser():
    description = (
        "Calculates the recovery factor given summary keys and dates.\n"
        "Requires an EclSum instance to retrieve the volumes from. The summary "
        "keys requested must be in the EclSum instance. If the dates are outside "
        "the simulation range, they will be clamped to nearest. Will throw an "
        "error if the entire date range is outside the simulation range\n\n"
        "It is up to the caller to use sane combinations of summary keys."
    )
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--summary", required=True, type=str, help="Ecl summary file")
    parser.add_argument(
        "--production_key",
        default="FOPT",
        type=str,
        help="Production key - a valid summary key",
    )
    parser.add_argument(
        "--total_volume_key",
        default="FOIP",
        type=str,
        help="Total volume key - a valid summary key",
    )
    parser.add_argument(
        "--start_date",
        default=None,
        type=str,
        help="Start date - A date string on the format DD.MM.YYYY",
    )
    parser.add_argument(
        "--end_date",
        default=None,
        type=str,
        help="Start date - A date string on the format DD.MM.YYYY",
    )
    parser.add_argument("--output_file", type=str, help="Filename of the output file. ")
    return parser


def main_entry_point():
    parser = rf_parser()
    args = parser.parse_args(sys.argv[1:])
    logger.info("Initializing recovery factor calculation")

    rf = recovery_factor(
        ecl_sum=args.summary,
        production_key=args.production_key,
        total_volume_key=args.total_volume_key,
        start_date=args.start_date,
        end_date=args.end_date,
    )

    with open(args.output_file, "w") as f:
        f.write("{0:.6f}".format(rf))


if __name__ == "__main__":
    main_entry_point()
