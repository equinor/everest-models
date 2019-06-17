#!/usr/bin/env python

import argparse
import datetime
import math
import os
import re
import sys
from itertools import compress

import yaml
from ecl.summary import EclSum

import configsuite
from spinningjenny import customized_logger
from spinningjenny.npv import npv_config
from spinningjenny.npv.npv_job import CalculateNPV

logger = customized_logger.get_logger(__name__)


def main_entry_point(args=None):
    if args is None:
        args = sys.argv[1:]

    npv_parser = _build_parser()
    options = npv_parser.parse_args(args=args)

    with open(options.config_file, "r") as config_file:
        input_data = yaml.safe_load(config_file)

    config = _prepare_config(input_data, options)

    logger.info("initializing npv calculation with options {}".format(options))
    npv = CalculateNPV(config.snapshot, options.summary_file)
    npv.run()
    npv.write()


def main(args):
    main_entry_point(args)


def _build_parser():
    description = (
        "Module to calculate the NPV based on an eclipse simulation. "
        "All optional args is also configurable through the config file"
    )
    arg_parser = argparse.ArgumentParser(description=description)
    arg_parser.add_argument(
        "--summary-file",
        required=True,
        type=_valid_file,
        help="Path to eclipse summary file to base your NPV calculation towards",
    )
    arg_parser.add_argument(
        "--config-file",
        required=True,
        type=_valid_file,
        help="Path to config file containing at least prices",
    )
    arg_parser.add_argument(
        "--output-file",
        type=str,
        help="Path to output-file where the NPV result is written to.",
    )
    arg_parser.add_argument(
        "--input-file", type=_valid_file, help="Path to input file."
    )
    arg_parser.add_argument(
        "--start-date",
        type=_valid_date,
        help="Startpoint of NPV calculation as ISO8601 formatted date (YYYY-MM-DD).",
    )
    arg_parser.add_argument(
        "--end-date",
        type=_valid_date,
        help="Endpoint of NPV calculation as ISO8601 formatted date (YYYY-MM-DD).",
    )
    arg_parser.add_argument(
        "--ref-date",
        type=_valid_date,
        help="Ref point of NPV calculation as ISO8601 formatted date (YYYY-MM-DD).",
    )
    arg_parser.add_argument(
        "--default-discount-rate",
        type=float,
        help="Default discount rate you want to use.",
    )
    arg_parser.add_argument(
        "--default-exchange-rate",
        type=float,
        help="Default exchange rate you want to use.",
    )
    arg_parser.add_argument(
        "--multiplier", type=int, help="Multiplier you want to use."
    )

    return arg_parser


def _valid_file(fname):
    if not os.path.isfile(fname):
        raise AttributeError("File was not found: {}".format(fname))
    return fname


def _valid_date(date):
    try:
        return datetime.datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        msg = "Not a valid ISO8601 formatted date (YYYY-MM-DD): '{}'.".format(date)
        raise argparse.ArgumentTypeError(msg)


def _prepare_config(input_data, options):
    # Purpose of this function is to make config file complete
    # by creating a configsuite instance with user config along with a
    # layer of default settings.
    #
    # If any args provided, we inject those and overrides whats currently
    # in the config file

    this_path = os.path.dirname(__file__)
    defaults_path = os.path.join(this_path, "..", "npv", "npv_defaults.yml")

    with open(defaults_path, "r") as defaults_file:
        defaults = yaml.safe_load(defaults_file)

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

    if options.output_file:
        logger.info("From args - 'output_file': {}".format(options.output_file))
        config = config.push({"files": {"output_file": options.output_file}})

    if options.input_file:
        logger.info("From args - 'input_file': {}".format(options.input_file))
        config = config.push({"files": {"input_file": options.input_file}})

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
    main(sys.argv[1:])
