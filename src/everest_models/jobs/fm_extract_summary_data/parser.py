from everest_models.jobs.fm_extract_summary_data.tasks import CalculationType
from everest_models.jobs.shared.arguments import (
    add_lint_argument,
    add_output_argument,
    add_summary_argument,
    get_parser,
)
from everest_models.jobs.shared.validators import valid_iso_date


def build_argument_parser(skip_type=False):
    description = "Module to extract Eclipse Summary keyword data for single date or date interval"
    parser, requird_group = get_parser(description=description)

    add_summary_argument(requird_group, skip_type=skip_type)
    add_output_argument(
        requird_group,
        help="Output file",
        skip_type=skip_type,
    )
    add_lint_argument(parser)
    parser.add_argument(
        "-sd",
        "--start-date",
        type=valid_iso_date,
        help="Start date, if not specified the module will write to the output "
        "file a single summary key value for the specified end date",
    )
    requird_group.add_argument(
        "-ed",
        "--end-date",
        "--date",
        type=valid_iso_date,
        required=True,
        help="End date for the summary key interval or date for which to "
        "extract a summary key value",
    )
    requird_group.add_argument(
        "-k", "--key", type=str, required=True, help="Eclipse summary key"
    )
    parser.add_argument(
        "-t",
        "--type",
        type=CalculationType,
        default="diff",
        choices=CalculationType.types(),
        help="Range calculation type to use",
    )
    parser.add_argument(
        "-m", "--multiplier", type=float, default=1, help="Result multiplier"
    )

    return parser


args_parser = build_argument_parser()
