import argparse
import logging
import os
from functools import partial

from spinningjenny import is_writable, valid_file
from spinningjenny.interpret_well_drill_job import interpret_well_drill

logger = logging.getLogger(__name__)


def interpret_well_drill_argparser():
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


def main_entry_point(args=None):
    arg_parser = interpret_well_drill_argparser()
    options = arg_parser.parse_args(args)

    interpret_well_drill(dakota_values_file=options.input, output_file=options.output)


if __name__ == "__main__":
    main_entry_point()
