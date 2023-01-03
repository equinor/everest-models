#!/usr/bin/env python

import argparse
import logging

from spinningjenny.jobs.fm_npv.manager import NPVCalculator
from spinningjenny.jobs.fm_npv.parser import build_argument_parser

logger = logging.getLogger(__name__)


def _overwrite_npv_config(options: argparse.Namespace, field: str, index: int = 1):
    if (value := getattr(options, field, None)) is not None:
        instance = options.config.dates if "date" in field else options.config
        setattr(instance, field, value[index] if isinstance(value, tuple) else value)
        logger.info(f"Overwrite config field with '{field}' CLI argument: {value}")


def main_entry_point(args=None):
    args_parser = build_argument_parser()
    options = args_parser.parse_args(args=args)

    if bool(options.config.well_costs) ^ bool(options.input):
        args_parser.error(
            "-c/--config argument file key 'well cost' and -i/--input argument file "
            "must always be paired; one of the two is missing."
        )

    if options.lint:
        args_parser.exit()

    for field in (
        "multiplier",
        "default_exchange_rate",
        "default_discount_rate",
        "start_date",
        "end_date",
        "ref_date",
    ):
        _overwrite_npv_config(options, field)

    logger.info(f"Initializing npv calculation with options {options}")
    npv = NPVCalculator(config=options.config, summary=options.summary).compute(
        {
            well.name: well.completion_date or well.readydate
            for well in options.input or {}
        }
    )

    options.output.write_text(f"{npv:.2f}")


if __name__ == "__main__":
    main_entry_point()
