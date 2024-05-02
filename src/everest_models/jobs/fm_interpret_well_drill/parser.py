from everest_models.jobs.shared.arguments import (
    add_input_argument,
    add_lint_argument,
    add_output_argument,
    get_parser,
)


def build_argument_parser():
    description = (
        "This module transforms dakota well_drill output to a json object."
        "This object contains a list of well names to keep."
    )

    parser, required_group = get_parser(description=description)
    add_input_argument(
        required_group,
        help=(
            "Yaml file that contains optimizer output, this should consist "
            "of a list of well names, with their associated value between 0 and 1"
        ),
    )
    add_lint_argument(parser)
    add_output_argument(
        required_group,
        help="File path to write the resulting json file to.",
    )

    return parser


args_parser = build_argument_parser()
