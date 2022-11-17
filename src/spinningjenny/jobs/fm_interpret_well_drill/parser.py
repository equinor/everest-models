import argparse
from functools import partial

from spinningjenny.jobs.shared.validators import is_writable, valid_file


def build_argument_parser():
    description = (
        "This module transforms dakota well_drill output to a json object."
        "This object contains a list of well names to keep."
    )

    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "-i",
        "--input",
        required=True,
        type=partial(valid_file, parser=parser),
        help=(
            "Yaml file that contains optimizer output, this should consist "
            "of a list of well names, with their associated value between 0 and 1"
        ),
    )
    parser.add_argument(
        "-o",
        "--output",
        required=True,
        type=partial(is_writable, parser=parser),
        help="File path to write the resulting json file to.",
    )

    return parser


args_parser = build_argument_parser()
