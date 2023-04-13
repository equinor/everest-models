from spinningjenny.jobs.shared.arguments import (
    add_lint_argument,
    add_output_argument,
    add_summary_argument,
    get_parser,
)
from spinningjenny.jobs.shared.validators import valid_iso_date


def build_argument_parser():
    parser, required_group = get_parser(
        description="Calculates the recovery factor given summary keys and dates.\n"
        "Requires an EclSum instance to retrieve the volumes from. The summary "
        "keys requested must be in the EclSum instance. If the dates are outside "
        "the simulation range, they will be clamped to nearest. Will throw an "
        "error if the entire date range is outside the simulation range."
    )
    add_summary_argument(required_group)
    add_lint_argument(parser)
    add_output_argument(parser, required=False, help="Filename of the output file. ")
    parser.add_argument(
        "-pk",
        "--production_key",
        default="FOPT",
        type=str,
        help="Production key - a valid summary key",
    )
    parser.add_argument(
        "-tvk",
        "--total_volume_key",
        default="FOIP",
        type=str,
        help="Total volume key - a valid summary key",
    )
    parser.add_argument(
        "-sd",
        "--start_date",
        type=valid_iso_date,
        help="Start date - As ISO8601 formatted date (YYYY-MM-DD)",
    )
    parser.add_argument(
        "-ed",
        "--end_date",
        type=valid_iso_date,
        help="Start date - As ISO8601 formatted date (YYYY-MM-DD)",
    )
    return parser


args_parser = build_argument_parser()
