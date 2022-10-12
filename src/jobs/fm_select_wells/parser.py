import argparse
import datetime
from functools import partial

from jobs.utils.validators import is_writable, valid_json_file


def build_argument_parser():
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


args_parser = build_argument_parser()
