#!/usr/bin/env python

import argparse
import os

import configsuite

from functools import partial

from spinningjenny import (
    customized_logger,
    valid_file,
    valid_date,
    valid_yaml_file,
    load_yaml,
)
from spinningjenny.npv import npv_config
from spinningjenny.npv.npv_job import CalculateNPV

logger = customized_logger.get_logger(__name__)


def main_entry_point(args=None):
    npv_parser = _build_parser()
    options = npv_parser.parse_args(args=args)

    config = _prepare_config(options.config, options)

    logger.info("initializing npv calculation with options {}".format(options))
    npv = CalculateNPV(config.snapshot, options.summary)
    npv.run()
    npv.write()


def _build_parser():
    description = (
        "Module to calculate the NPV based on an eclipse simulation. "
        "All optional args is also configurable through the config file"
    )
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "-s",
        "--summary",
        required=True,
        type=partial(valid_file, parser=parser),
        help="Path to eclipse summary file to base your NPV calculation towards",
    )
    parser.add_argument(
        "-c",
        "--config",
        required=True,
        type=partial(valid_yaml_file, parser=parser),
        help="Path to config file containing at least prices",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        help="Path to output-file where the NPV result is written to.",
    )
    parser.add_argument(
        "-i",
        "--input",
        type=partial(valid_file, parser=parser),
        help="Path to input file.",
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


def _prepare_config(input_data, options):
    # Purpose of this function is to make config file complete
    # by creating a configsuite instance with user config along with a
    # layer of default settings.
    #
    # If any args provided, we inject those and overrides whats currently
    # in the config file

    this_path = os.path.dirname(__file__)
    defaults_path = os.path.join(this_path, "..", "npv", "npv_defaults.yml")

    defaults = load_yaml(defaults_path)

    schema = npv_config._build_schema()
    config = configsuite.ConfigSuite(input_data, schema, layers=(defaults,))

    if options.default_discount_rate:
        logger.info(
            "From args - 'default_discount_rate': {}".format(
                options.default_discount_rate
            )
        )
        config = config.push({"default_discount_rate": options.default_discount_rate})

    if options.default_exchange_rate:
        logger.info(
            "From args - 'default_exchange_rate': {}".format(
                options.default_exchange_rate
            )
        )
        config = config.push({"default_exchange_rate": options.default_exchange_rate})

    if options.multiplier:
        logger.info("From args - 'multiplier': {}".format(options.multiplier))
        config = config.push({"multiplier": options.multiplier})

    if options.output:
        logger.info("From args - 'output': {}".format(options.output))
        config = config.push({"files": {"output_file": options.output}})

    if options.input:
        logger.info("From args - 'input': {}".format(options.input))
        config = config.push({"files": {"input_file": options.input}})

    if options.start_date:
        logger.info("From args - 'start_date': {}".format(options.start_date))
        config = config.push({"dates": {"start_date": options.start_date}})

    if options.end_date:
        logger.info("From args - 'end_date': {}".format(options.end_date))
        config = config.push({"dates": {"end_date": options.end_date}})

    if options.ref_date:
        logger.info("From args - 'ref_date': {}".format(options.ref_date))
        config = config.push({"dates": {"ref_date": options.ref_date}})

    if not config.valid:
        for error in config.errors:
            logger.error(error)
        assert config.valid

    return config


if __name__ == "__main__":
    main_entry_point()
