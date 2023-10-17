from functools import partial

from everest_models.jobs.shared.arguments import (
    add_output_argument,
    add_wells_input_argument,
    bootstrap_parser,
    get_parser,
)
from everest_models.jobs.shared.validators import is_gt_zero, valid_input_file


@bootstrap_parser
def build_argument_parser():
    parser, required_group = get_parser(
        description="Calculate and write drill times from scaled controls.",
    )
    add_wells_input_argument(
        required_group,
        help="Wells file generated by Everest (wells.json).",
    )
    add_output_argument(
        required_group,
        help="Output file: input for drill planner job.",
    )
    required_group.add_argument(
        "-opt",
        "--optimizer",
        required=True,
        type=valid_input_file,
        help="File containing information related to wells. The format is "
        "consistent with the wells.json file when running everest and can "
        "be used directly.",
    )
    required_group.add_argument(
        "-b",
        "--bounds",
        required=True,
        type=float,
        metavar=("UPPER", "LOWER"),
        help="Upper and lower bounds of the controls.",
        nargs=2,
    )
    required_group.add_argument(
        "-m",
        "--max-days",
        required=True,
        type=partial(is_gt_zero, msg="max-days must be > 0"),
        help="Maximum time interval in days.",
    )
    return parser
