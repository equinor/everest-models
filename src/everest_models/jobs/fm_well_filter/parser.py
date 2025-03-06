from everest_models.jobs.shared.arguments import (
    add_output_argument,
    add_wells_input_argument,
    bootstrap_parser,
    get_parser,
)
from everest_models.jobs.shared.validators import valid_input_file


@bootstrap_parser
def build_argument_parser(skip_type=False):
    parser, required_group = get_parser(
        prog="fm_well_filter",
        description="This module filters out wells using a json string."
        "Either the --keep or the --remove flag needs to be set to a json file name"
        "containing a list of well names that are in the keep/remove file, "
        "but not in the input file will be ignored."
        "If both or none of the flags are set, the job give an error.",
    )
    add_wells_input_argument(
        required_group,
        help=(
            "Json file that contains a list of dictionaries containing well information."
        ),
        skip_type=skip_type,
    )
    add_output_argument(
        required_group,
        help="File path to write the resulting wells file to.",
        skip_type=skip_type,
    )
    group = required_group.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "-k",
        "--keep",
        type=valid_input_file if not skip_type else str,
        help="JSON/Y(A)ML file that contains a list of well names to keep.",
    )
    group.add_argument(
        "-r",
        "--remove",
        type=valid_input_file if not skip_type else str,
        help="JSON/Y(A)ML file that contains a list of well names to remove.",
    )
    return parser
