import argparse
import os

from functools import partial

from spinningjenny.schmerge_job import merge_schedule, get_transformed_injections
from spinningjenny import customized_logger, valid_file, valid_json_file, is_writable

logger = customized_logger.get_logger(__name__)


def valid_schmerge_config(file_path, parser):
    json_dict = valid_json_file(file_path, parser)
    try:
        injections = get_transformed_injections(json_dict)
        return injections
    except KeyError as e:
        parser.error(
            "Json file <{}> misses a required keyword: {}".format(file_path, str(e))
        )


def schmerge_argparser():
    description = (
        "This module works on a schedule file intended for reservoir simulation"
        "(e.g. eclipse or flow), and injects templates at given dates. If the report"
        "date does not exist in advance it will be added as an independent step. "
        "The templates will further be filled in with the given parameter values."
    )

    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "-i",
        "--input",
        required=True,
        type=partial(valid_file, parser=parser),
        help="Input schedule file to inject templates into. The only currently"
        " accepted date format is the following: one line consisting of the"
        " DATES keyword, followed by a date in the format of '1 JAN 2000'"
        " terminated by a slash. The final line consists of a slash."
        " An empty line should be in between the date format and anything below.",
    )
    parser.add_argument(
        "-c",
        "--config",
        required=True,
        type=partial(valid_schmerge_config, parser=parser),
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
        "-o",
        "--output",
        required=True,
        type=partial(is_writable, parser=parser),
        help="File path to write the resulting schedule file to.",
    )

    return parser


def main_entry_point(args=None):
    arg_parser = schmerge_argparser()
    options = arg_parser.parse_args(args)

    merge_schedule(
        schedule_file=options.input,
        injections=options.config,
        output_file=options.output,
    )


if __name__ == "__main__":
    main_entry_point()
