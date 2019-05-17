import argparse
import os
import sys
from spinningjenny.schmerge_job import merge_schedule
from spinningjenny import customized_logger

logger = customized_logger.get_logger(__name__)


def schmerge_argparser():
    description = (
        "This module works on a schedule file intended for reservoir simulation"
        "(e.g. eclipse or flow), and injects templates at given dates. If the report"
        "date does not exist in advance it will be added as an independent step. "
        "The templates will further be filled in with the given parameter values."
    )

    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "--schedule-input",
        required=True,
        type=_valid_file,
        help="Input schedule file to inject templates into. The only currently"
        " accepted date format is the following: one line consisting of the"
        " DATES keyword, followed by a date in the format of '1 JAN 2000'"
        " terminated by a slash. The final line consists of a slash."
        " An empty line should be in between the date format and anything below.",
    )
    parser.add_argument(
        "--config",
        required=True,
        type=_valid_file,
        help=(
            "Json file that specifies which templates to inject where."
            "The file is structured as a list of dictionaries, each containing"
            " information regarding one well. The name defines the name of the well,"
            " and the ops is a list of operations to be performed on the well."
            " The operations are defined within a dict with the required keys template,"
            " date and any parameter values that are to be injected into the given template"
        ),
    )
    parser.add_argument(
        "--schedule-output",
        required=True,
        type=_writable_location,
        help="File path to write the resulting schedule file to.",
    )

    return parser


def _valid_file(fname):
    if not os.path.isfile(fname):
        raise AttributeError("File was not found: {}".format(fname))
    return fname


def _writable_location(fname):
    with open(fname, "w") as _:
        pass
    os.remove(fname)
    return fname


def main_entry_point(args=None):
    if args is None:
        args = sys.argv[1:]
    arg_parser = schmerge_argparser()
    args, _ = arg_parser.parse_known_args(args=args)

    merge_schedule(
        schedule_file=args.schedule_input,
        inject_file=args.config,
        output_file=args.schedule_output,
    )


if __name__ == "__main__":
    main_entry_point()
