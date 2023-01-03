from functools import partial

from spinningjenny.jobs.fm_npv.npv_config_model import NPVConfig
from spinningjenny.jobs.shared.arguments import (
    SchemaAction,
    add_output_argument,
    add_summary_argument,
    add_wells_input_argument,
    bootstrap_parser,
)
from spinningjenny.jobs.shared.validators import parse_file, valid_iso_date

CONFIG_ARGUMENT = ["-c", "--config"]


def build_argument_parser():
    SchemaAction.register_single_model("/".join(CONFIG_ARGUMENT), NPVConfig)
    parser, required_group = bootstrap_parser(
        description="Module to calculate the NPV based on an eclipse simulation. "
        "All optional args, except: lint, schemas, input and output, is also configurable through the config file."
    )
    add_summary_argument(required_group)
    add_wells_input_argument(
        parser,
        required=False,
        help="Path to input file containing information related to wells. "
        "The format is consistent with the wells.json file when running "
        "everest. It must contain a 'readydate' key for each well for when "
        "it is considered completed and ready for production.",
    )
    add_output_argument(
        parser,
        required=False,
        default="npv_0",
        help="Path to output-file where the NPV result is written to.",
    )
    required_group.add_argument(
        *CONFIG_ARGUMENT,
        required=True,
        type=partial(parse_file, schema=NPVConfig),
        help="Path to config file containing at least prices",
    )
    parser.add_argument(
        "-sd",
        "--start-date",
        type=valid_iso_date,
        help="Start point of NPV calculation as ISO8601 formatted date (YYYY-MM-DD).",
    )
    parser.add_argument(
        "-ed",
        "--end-date",
        type=valid_iso_date,
        help="End point of NPV calculation as ISO8601 formatted date (YYYY-MM-DD).",
    )
    parser.add_argument(
        "-rd",
        "--ref-date",
        type=valid_iso_date,
        help="Ref point of NPV calculation as ISO8601 formatted date (YYYY-MM-DD).",
    )
    parser.add_argument(
        "-ddr",
        "--default-discount-rate",
        type=float,
        help="Default discount rate you want to use.",
    )
    parser.add_argument(
        "-der",
        "--default-exchange-rate",
        type=float,
        help="Default exchange rate you want to use.",
    )
    parser.add_argument("--multiplier", type=int, help="Multiplier you want to use.")

    return parser
