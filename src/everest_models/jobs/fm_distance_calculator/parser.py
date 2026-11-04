import argparse
from pathlib import Path

from everest_models.jobs.shared.arguments import bootstrap_parser, get_parser


@bootstrap_parser
def build_argument_parser(skip_type: bool = False) -> argparse.ArgumentParser:
    parser, required_group = get_parser(
        description="Calculate distances to faults, wells, or configured polylines."
    )
    required_group.add_argument(
        "-c",
        "--config",
        required=True,
        type=Path if not skip_type else str,
        help="Distance calculation configuration file in YAML format.",
    )
    model_group = parser.add_argument_group("case input")
    model_group.add_argument(
        "-cn",
        "--case-name",
        dest="case_name",
        type=Path if not skip_type else str,
        help="Case base path, for example model/CASE (reads model/CASE.EGRID).",
    )
    model_group.add_argument(
        "--egrid",
        type=Path if not skip_type else str,
        help="Path to an EGRID file; overrides -cn/--case-name when both are given.",
    )
    parser.add_argument(
        "--resinsight",
        default="",
        help="Path to ResInsight executable; otherwise use rips configuration or $RESINSIGHT_EXECUTABLE.",
    )
    return parser
