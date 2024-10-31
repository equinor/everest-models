from everest_models.jobs.shared.arguments import (
    add_output_argument,
    add_wells_input_argument,
    bootstrap_parser,
    get_parser,
)
from everest_models.jobs.shared.validators import valid_schedule_template

from .well_model import Wells


@bootstrap_parser
def build_argument_parser(skip_type=False):
    parser, required_group = get_parser(
        description="This module works on a schedule file intended for reservoir simulation"
        "(e.g. eclipse or flow), and injects templates at given dates. If the report"
        "date does not exist in advance it will be added as an independent step. "
        "The templates will further be filled in with the given parameter values."
    )
    required_group.add_argument(
        "-s",
        "--schedule",
        required=True,
        type=valid_schedule_template if not skip_type else str,
        help="Schedule file to inject templates into. The only currently"
        " accepted date format is the following: one line consisting of the"
        " DATES keyword, followed by a date in the format of '1 JAN 2000'"
        " terminated by a slash. The final line consists of a slash."
        " An empty line should be in between the date format and anything below.",
    )
    add_wells_input_argument(
        required_group,
        schema=Wells,
        help="Json file that specifies which templates to inject where."
        "The file is structured as a list of dictionaries, each containing"
        " information regarding one well. The name defines the name of the well,"
        " and the ops is a list of operations to be performed on the well."
        " The operations are defined within a dict with the required keys template,"
        " date and any parameter values that are to be injected into the given template",
        skip_type=skip_type,
    )
    add_output_argument(
        required_group,
        help="File path to write the resulting schedule file to.",
        skip_type=skip_type,
    )
    return parser
