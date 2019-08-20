import os
import argparse
from functools import partial
from spinningjenny.well_filter_job import filter_wells
from spinningjenny import customized_logger, valid_file, touch_filename

logger = customized_logger.get_logger(__name__)


def filter_argparser():
    description = (
        "This module filters out wells using a json string."
        "Either the --keep or the --remove flag needs to be set to a json file name"
        "containing a list of well names that are in the keep/remove file, "
        "but not in the input file will be ignored."
        "If both or none of the flags are set, the job give an error."
    )

    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "-i",
        "--input",
        required=True,
        type=partial(valid_file, parser=parser),
        help=(
            "Json file that contains a list of dictionaries containing well information."
        ),
    )
    parser.add_argument(
        "-k",
        "--keep",
        required=False,
        default=None,
        type=partial(valid_file, parser=parser),
        help="Json file that contains a list of well names to keep.",
    )
    parser.add_argument(
        "-r",
        "--remove",
        required=False,
        default=None,
        type=partial(valid_file, parser=parser),
        help="Json file that contains a list of well names to remove.",
    )
    parser.add_argument(
        "-o",
        "--output",
        required=True,
        type=touch_filename,
        help="File path to write the resulting wells file to.",
    )

    return parser


def main_entry_point(args=None):
    arg_parser = filter_argparser()
    options = arg_parser.parse_args(args)

    filter_wells(
        wells_file=options.input,
        output_file=options.output,
        keep_file=options.keep,
        remove_file=options.remove,
    )


if __name__ == "__main__":
    main_entry_point()
