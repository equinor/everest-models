import argparse
from functools import partial

from spinningjenny.jobs.utils.validators import is_writable, valid_json_file


def build_argument_parser():
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
        type=partial(valid_json_file, parser=parser),
        help=(
            "Json file that contains a list of dictionaries containing well information."
        ),
    )
    parser.add_argument(
        "-k",
        "--keep",
        default=None,
        type=partial(valid_json_file, parser=parser),
        help="Json file that contains a list of well names to keep.",
    )
    parser.add_argument(
        "-r",
        "--remove",
        default=None,
        type=partial(valid_json_file, parser=parser),
        help="Json file that contains a list of well names to remove.",
    )
    parser.add_argument(
        "-o",
        "--output",
        required=True,
        type=partial(is_writable, parser=parser),
        help="File path to write the resulting wells file to.",
    )

    return parser


args_parser = build_argument_parser()
