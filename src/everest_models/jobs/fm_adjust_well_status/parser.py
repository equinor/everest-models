from ..shared.arguments import add_output_argument, add_wells_input_argument, get_parser
from ..shared.io_utils import load_json


def build_argument_parser():
    parser, required_group = get_parser(description="Adjust well status")
    add_wells_input_argument(required_group)
    add_output_argument(
        required_group, help="name of output file containing well status switches"
    )
    required_group.add_argument(
        "-s", "--switch", type=load_json, help="name of input well switch file"
    )
    required_group.add_argument(
        "-sd",
        "--switch-dict",
        type=load_json,
        help="name of input file containing switch status dictionary",
    )

    return parser


args_parser = build_argument_parser()
