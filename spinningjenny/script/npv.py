#!/usr/bin/python
# -*- coding: utf-8 -*-
import argparse
import datetime
import math
import os.path
import re
import sys
from itertools import compress

from ecl.summary import EclSum

import yaml
from spinningjenny import customized_logger
from spinningjenny.npv_job import CalculateNPV

logger = customized_logger.get_logger(__name__)

_DEFAULT_OUTPUT_FILE = 'npv_0'
_DEFAULT_T2S_FILE = 't2s_npv_info'
_DEFAULT_DISCOUNT_RATE = 0.08
_DEFAULT_EXCHANGE_RATE = 1
_MULTIPLIER = 1


def main_entry_point(args=None):
    if args is None:
        args = sys.argv

    options = _extract_options(args)

    with open(options.config_file, 'r') as config_file:
        input_data = yaml.safe_load(config_file)

    _prepare_config(input_data, options)

    logger.info("initializing npv calculation with options {}".format(options))
    npv = CalculateNPV(input_data)
    npv.run()
    npv.write()

def main(args):
    main_entry_point(args)


def _extract_options(args):
    description = (
        'Module to calculate the NPV based on an eclipse simulation'
    )
    arg_parser = argparse.ArgumentParser(description=description)
    arg_parser.add_argument('--summary-file',
                            required=True,
                            type=_valid_file,
                            help='Path to eclipse summary file to base your NPV calculation towards')
    arg_parser.add_argument('--config-file',
                            required=True,
                            type=_valid_file,
                            help="Path to config file containing at least prices")
    arg_parser.add_argument('--output-file',
                            default=None,
                            type=str,
                            help="Path to output-file where the NPV result is written to. If not specified in args or config, default is '{}'".format(_DEFAULT_OUTPUT_FILE))
    arg_parser.add_argument('--t2s-file',
                            default=None,
                            type=_valid_file,
                            help="Path to t2s-file. If not specified in args or config, default is '{}'".format(_DEFAULT_T2S_FILE))
    arg_parser.add_argument('--start-date',
                            default=None,
                            type=str,
                            help="Startpoint of NPV calculation. Format dd.MM.yyyy. Defaults to simulation start time")
    arg_parser.add_argument('--end-date',
                            default=None,
                            type=str,
                            help="Endpoint of NPV calculation. Format dd.MM.yyyy. Defaults to simulation end time")
    arg_parser.add_argument('--ref-date',
                            default=None,
                            type=str,
                            help="Ref point of NPV calculation. Format dd.MM.yyyy. Defaults to simulation start time")
    arg_parser.add_argument('--default-discount-rate',
                            default=None,
                            type=str,
                            help="Default discount rate you want to use. If not specified in args or config, default is {}".format(_DEFAULT_DISCOUNT_RATE))
    arg_parser.add_argument('--default-exchange-rate',
                            default=None,
                            type=str,
                            help="Default exchange rate you want to use. If not specified in args or config, default is {}".format(_DEFAULT_EXCHANGE_RATE))
    arg_parser.add_argument('--multiplier',
                            default=None,
                            type=int,
                            help="Multiplier you want to use. If not specified in args or config, default is {}".format(_MULTIPLIER))

    options, _ = arg_parser.parse_known_args(args=args)
    return options


def _valid_file(fname):
    if not os.path.isfile(fname):
        raise AttributeError("File was not found: {}".format(fname))
    return fname


def _prepare_config(input_data, options):
    # Purpose of this function is to make the config file complete
    # Some values can be provided both through config and args
    # Some values can be provided only through config
    # Some values can only be provided through args
    # If provided through args - value in config is always overridden if exists
    # Some values defaults to an internal defined value if not provided in either config or args

    _use_option_or_config(input_data, 'default_discount_rate',
                          options.default_discount_rate, default=_DEFAULT_DISCOUNT_RATE)
    _use_option_or_config(input_data, 'default_exchange_rate',
                          options.default_exchange_rate, default=_DEFAULT_EXCHANGE_RATE)
    _use_option_or_config(input_data, 'multiplier',
                          options.multiplier, default=_MULTIPLIER)

    files = input_data.get('files', {})

    # summary_file and config_file is required through argparse - do not have any defaults
    if 'summary_file' in files:
        logger.warn(
            "summary_file need to be provided as arg through cli, your option provided in config file will not be used")
    files['summary_file'] = options.summary_file
    if 'config_file' in files:
        logger.warn(
            "config_file need to be provided as arg through cli, your option provided in config file will not be used")
    files['config_file'] = options.config_file

    _use_option_or_config(files, 'output_file',
                          options.output_file, default=_DEFAULT_OUTPUT_FILE)
    _use_option_or_config(
        files, 't2s_file', options.t2s_file, default=_DEFAULT_T2S_FILE)

    dates = input_data.get('dates', {})

    # dates are optional in both args and config - defaults in code to simulation start and end times
    _use_option_or_config(dates, 'start_date', options.start_date)
    _use_option_or_config(dates, 'end_date', options.end_date)
    _use_option_or_config(dates, 'ref_date', options.ref_date)


def _use_option_or_config(root, name, option, default=None):
    if option:
        logger.debug(
            "Configuring {} from args with value {}".format(name, option))
        root[name] = option
    elif name not in root and default:
        logger.debug("Adding default value {} for {}".format(default, name))
        root[name] = default


if __name__ == "__main__":
    main(sys.argv[1:])
