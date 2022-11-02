import argparse
from functools import partial

from spinningjenny.jobs.fm_schmerge.tasks import get_transformed_injections
from spinningjenny.jobs.utils.validators import is_writable, valid_file, valid_json_file


def valid_schmerge_config(file_path, parser):
    json_dict = valid_json_file(file_path, parser)
    try:
        injections = get_transformed_injections(json_dict)
        return injections
    except KeyError as e:
        parser.error(
            "Json file <{}> misses a required keyword: {}".format(file_path, str(e))
        )


def build_argument_parser():
    description = (
        "This module works on a schedule file intended for reservoir simulation"
        "(e.g. eclipse or flow), and injects templates at given dates. If the report"
        "date does not exist in advance it will be added as an independent step. "
        "The templates will further be filled in with the given parameter values."
    )

    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "-s",
        "--schedule",
        required=True,
        type=partial(valid_file, parser=parser),
        help="Schedule file to inject templates into. The only currently"
        " accepted date format is the following: one line consisting of the"
        " DATES keyword, followed by a date in the format of '1 JAN 2000'"
        " terminated by a slash. The final line consists of a slash."
        " An empty line should be in between the date format and anything below.",
    )
    parser.add_argument(
        "-i",
        "--input",
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


args_parser = build_argument_parser()
