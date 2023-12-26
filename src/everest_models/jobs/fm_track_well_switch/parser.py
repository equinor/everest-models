from ..shared.arguments import add_output_argument, get_parser
from ..shared.io_utils import load_json


def build_argument_parser():
    parser, required_group = get_parser(description="Adjust well status")
    add_output_argument(required_group, help="name of output well switch file")
    required_group.add_argument(
        "-s", "--switch", type=load_json, help="name of input well switch file"
    )
    parser.add_argument(
        "-p",
        "--priority",
        type=load_json,
        default=None,
        help="name of input well priority file",
    )
    required_group.add_argument(
        "-inj",
        "--number-of-injectors",
        type=lambda x: load_json(x)["n"],
        help="name of input well number file",
    )
    required_group.add_argument(
        "-ar",
        "--allow-reopen",
        action="store_true",
        help="flag to allow shut converted wells to reopen",
    )

    return parser


args_parser = build_argument_parser()
