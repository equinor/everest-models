#!/usr/bin/env python

import logging

from jobs.fm_npv.parser import args_parser
from jobs.fm_npv.tasks import CalculateNPV

logger = logging.getLogger(__name__)


def main_entry_point(args=None):
    options = args_parser.parse_args(args=args)

    config = _prepare_config(options)
    if not config.valid:
        args_parser.error(
            "Invalid config file:\n{}".format(
                "\n".join([err.msg for err in config.errors])
            )
        )
    if config.snapshot.well_costs and options.input is None:
        args_parser.error("Well costs specified, but the -i/--input flag is missing")

    logger.info("initializing npv calculation with options {}".format(options))
    npv = CalculateNPV(config.snapshot, options.summary)
    npv.run()
    npv.write()


def _prepare_config(options):
    # Purpose of this function is to make config file complete
    # by creating a configsuite instance with user config along with a
    # layer of default settings.
    #
    # If any args provided, we inject those and overrides whats currently
    # in the config file

    config = options.config

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

    return config


if __name__ == "__main__":
    main_entry_point()
