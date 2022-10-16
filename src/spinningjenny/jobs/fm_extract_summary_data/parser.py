import argparse
from functools import partial

from spinningjenny.jobs.fm_extract_summary_data.utils import CalculationType
from spinningjenny.jobs.utils.validators import is_writable, valid_date, valid_ecl_file


def build_argument_parser():
    description = "Module to extract Eclipse Summary keyword data for single date or date interval"
    parser = argparse.ArgumentParser(description=description)

    parser.add_argument(
        "-s",
        "--summary",
        type=partial(valid_ecl_file, parser=parser),
        required=True,
        help="Eclipse summary file",
    )
    parser.add_argument(
        "-sd",
        "--start-date",
        type=partial(valid_date, parser=parser),
        help="Start date, if not specified the module will write to the output "
        "file a single summary key value for the specified end date",
    )
    parser.add_argument(
        "-ed",
        "--end-date",
        "--date",
        type=partial(valid_date, parser=parser),
        required=True,
        help="End date for the summary key interval or date for which to "
        "extract a summary key value",
    )
    parser.add_argument(
        "-k", "--key", type=str, required=True, help="Eclipse summary key"
    )
    parser.add_argument(
        "-t",
        "--type",
        type=str,
        default="diff",
        choices=CalculationType.types(),
        help="Type of range calculation to use one of (max or diff)",
    )
    parser.add_argument(
        "-m", "--multiplier", type=float, default=1, help="Result multiplier"
    )
    parser.add_argument(
        "-o",
        "--output",
        required=True,
        type=partial(is_writable, parser=parser),
        help="Output file",
    )

    return parser


args_parser = build_argument_parser()
