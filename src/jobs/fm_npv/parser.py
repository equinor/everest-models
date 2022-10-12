import argparse
from functools import partial

import pkg_resources

from jobs.fm_npv.schemas import build_schema
from jobs.utils.validators import (
    is_writable,
    load_yaml,
    valid_config,
    valid_date,
    valid_ecl_file,
    valid_file,
)


def _npv_default():
    defaults_path = pkg_resources.resource_filename(
        "jobs.fm_npv", "data/npv_defaults.yml"
    )

    return load_yaml(defaults_path)


def build_argument_parser():
    description = (
        "Module to calculate the NPV based on an eclipse simulation. "
        "All optional args is also configurable through the config file"
    )
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "-s",
        "--summary",
        required=True,
        type=partial(valid_ecl_file, parser=parser),
        help="Path to eclipse summary file to base your NPV calculation towards",
    )
    parser.add_argument(
        "-c",
        "--config",
        required=True,
        type=partial(
            valid_config, schema=build_schema(), parser=parser, layers=(_npv_default(),)
        ),
        help="Path to config file containing at least prices",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=partial(is_writable, parser=parser),
        help="Path to output-file where the NPV result is written to.",
    )
    parser.add_argument(
        "-i",
        "--input",
        required=False,
        type=partial(valid_file, parser=parser),
        help="Path to input file containing information related to wells. "
        "The format is consistent with the wells.json file when running "
        "everest. It must contain a 'readydate' key for each well for when "
        "it is considered completed and ready for production.",
    )
    parser.add_argument(
        "-sd",
        "--start-date",
        type=partial(valid_date, parser=parser),
        help="Startpoint of NPV calculation as ISO8601 formatted date (YYYY-MM-DD).",
    )
    parser.add_argument(
        "-ed",
        "--end-date",
        type=partial(valid_date, parser=parser),
        help="Endpoint of NPV calculation as ISO8601 formatted date (YYYY-MM-DD).",
    )
    parser.add_argument(
        "-rd",
        "--ref-date",
        type=partial(valid_date, parser=parser),
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


args_parser = build_argument_parser()
