import argparse
import logging
from functools import partial

from jobs.fm_well_filter.tasks import filter_wells, write_results
from jobs.utils.validators import is_writable, valid_json_file

logger = logging.getLogger(__name__)


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


def main_entry_point(args=None):
    arg_parser = filter_argparser()
    options = arg_parser.parse_args(args)

    filtered_wells = filter_wells(
        wells=options.input,
        parser=arg_parser,
        keep_wells=options.keep,
        remove_wells=options.remove,
    )

    write_results(filtered_wells, options.output)


if __name__ == "__main__":
    main_entry_point()
