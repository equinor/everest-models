from everest_models.jobs.shared.arguments import (
    add_lint_argument,
    add_summary_argument,
    get_parser,
)
from everest_models.jobs.shared.validators import valid_ecl_summary, valid_iso_date


def _valid_ecl_file(value: str):
    return valid_ecl_summary(value), value


def build_argument_parser(skip_type=False):
    description = (
        "Makes sure a given summary file contains only report steps at the "
        "list of dates given as an argument"
    )
    parser, required_group = get_parser(description=description, prog="fm_strip_dates")

    add_summary_argument(required_group, func=_valid_ecl_file, skip_type=skip_type)
    add_lint_argument(parser)
    parser.add_argument(
        "-d",
        "--dates",
        nargs="+",  # 1 or more values expected => creates a list
        metavar=("DATE1", "DATE2"),
        type=valid_iso_date,
        help="List of date to remain in the summary file",
        default=[],
    )

    parser.add_argument(
        "--allow-missing-dates",
        action="store_true",
        help="Do not fail if any requested dates are missing in the file",
    )

    return parser


args_parser = build_argument_parser()
