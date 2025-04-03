import datetime
from functools import partial

from everest_models.jobs.fm_select_wells.well_number_model import WellNumber
from everest_models.jobs.shared.arguments import (
    SchemaAction,
    add_output_argument,
    add_wells_input_argument,
    bootstrap_parser,
    get_parser,
)
from everest_models.jobs.shared.validators import is_gtoet_zero, parse_file


def scaled_well_number(value: str) -> float:
    return parse_file(value, WellNumber).scaled_number_of_wells


@bootstrap_parser
def build_argument_parser(skip_type=False):
    SchemaAction.register_models({"file": WellNumber})
    parser, required_named_arguments = get_parser(
        description="Select the first wells from a drill planner output file."
    )
    sub_parser = parser.add_subparsers(
        title="well number",
        description=(
            "Pass the number of wells to be selected as a value or a file path."
            " If neither, then `-m/--max-date` is required and the whole list of wells,"
            " bounded by the max date, is returned."
        ),
        required=False,
    )
    add_wells_input_argument(
        required_named_arguments,
        help="Input file: a drill planner output file.",
        skip_type=skip_type,
    )
    add_output_argument(
        required_named_arguments,
        help="Output file: updated drill planner output file",
        skip_type=skip_type,
    )
    parser.add_argument(
        "-m",
        "--max-date",
        type=datetime.date.fromisoformat,
        help="Maximum allowed date",
    )
    value = sub_parser.add_parser("value", help="The number of wells as a value")
    value.add_argument(
        "well_number",
        type=partial(is_gtoet_zero, msg="well number must be >= 0"),
        help="A positive integer for the number of wells to be selected.",
    )
    well_number_file = sub_parser.add_parser(
        "file",
        help="Everest control file containing the number of wells.",
    )
    sub_required_named_args = well_number_file.add_argument_group(
        "required named arguments"
    )
    well_number_file.add_argument(
        "file_path",
        type=scaled_well_number if not skip_type else str,
    )
    sub_required_named_args.add_argument(
        "-r",
        "--real-bounds",
        metavar=("LOWER", "UPPER"),
        type=int,
        help="Lower and upper bounds for the well number.",
        required=True,
        nargs=2,
    )
    sub_required_named_args.add_argument(
        "-s",
        "--scaled-bounds",
        metavar=("LOWER", "UPPER"),
        type=float,
        help="Scaled lower and upper bounds for the well number.",
        required=True,
        nargs=2,
    )
    return parser
