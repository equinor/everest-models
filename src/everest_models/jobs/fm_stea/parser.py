from pathlib import Path

import stea

from everest_models.jobs.shared.arguments import add_lint_argument, get_parser


def build_argument_parser(skip_type=False):
    description = (
        "STEA is a powerful economic analysis tool used for complex economic "
        "analysis and portfolio optimization. STEA helps you analyze single "
        "projects, large and small portfolios and complex decision trees. "
        "As output, for each of the entries in the result section of the "
        "yaml config file, STEA will create result files "
        "ex: Res1, Res2, .. Res#"
    )
    parser, required_group = get_parser(description=description)
    add_lint_argument(parser)
    required_group.add_argument(
        "-c",
        "--config",
        type=lambda value: stea.SteaInput(Path(value)) if not skip_type else str,
        help="STEA (yaml) config file",
        required=True,
    )
    return parser


args_parser = build_argument_parser()
