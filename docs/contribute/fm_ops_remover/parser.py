from spinningjenny.jobs.shared.arguments import (
    add_output_argument,
    add_wells_input_argument,
    bootstrap_parser,
)


def build_argument_parser():
    parser, required_group = bootstrap_parser(
        description="Given everest generated wells.json file"
        "and a list of well names. remove the intersecting names' operations."
    )
    add_wells_input_argument(required_group, help="Everest generated wells.json file")
    add_output_argument(required_group, help="Output File")
    required_group.add_argument(
        "-w", "--wells", required=True, help="wells to modified.", nargs="+", type=str
    )
    return parser
