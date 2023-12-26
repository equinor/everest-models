from ..shared.arguments import add_input_argument, add_output_argument, get_parser
from ..shared.io_utils import load_json


def build_argument_parser():
    parser, required_group = get_parser(
        description="Merge two wells.json type of files and update dates"
    )
    add_input_argument(required_group, nargs="+")
    add_output_argument(required_group, help="name of output well switch file")
    required_group.add_argument(
        "-d", "--dates", type=load_json, help=".json file with dates"
    )
    return parser


args_parser = build_argument_parser()
