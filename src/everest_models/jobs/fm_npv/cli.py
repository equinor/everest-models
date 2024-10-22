#!/usr/bin/env python

import argparse
import logging

from everest_models.jobs.fm_npv.manager import NPVCalculator
from everest_models.jobs.fm_npv.parser import build_argument_parser

logger = logging.getLogger(__name__)

FULL_JOB_NAME = "Net present value"

EXAMPLES = """
Argument examples
~~~~~~~~~~~~~~~~~

:code:`-config` example

.. code-block:: yaml

    prices:
        FOPT:
            - { date: 1999-01-01, value: 60, currency: USD }
        FWPT:
            - { date: 1999-01-01, value: -5, currency: USD }
            - { date: 2002-01-01, value: -2 }
        FGPT:
            - { date: 1999-01-01, value: 1, currency: USD }
            - { date: 2002-01-01, value: 0.1 }
        FWIT:
            - { date: 1999-01-01, value: -10, currency: USD }
            - { date: 2002-01-01, value: -20 }
        FGIT:
            - { date: 1999-01-01, value: -0.02, currency: USD }
            - { date: 2002-01-01, value: -0.1 }
        GOPT:OP:
            - { date: 1999-12-10, value: 555 }

    dates:
        start_date: 2000-12-06
        end_date: 2002-12-23
        ref_date: 2000-12-06

    summary_keys: ['FWIT', 'FOPT']

    exchange_rates:
        USD:
            - { date: 1997-01-01, value: 5 }
            - { date: 2000-02-01, value: 7 }
            - { date: 2001-05-01, value: 6 }
            - { date: 2002-02-01, value: 9 }

    discount_rates:
        - { date: 1999-01-01, value: 0.02 }
        - { date: 2002-01-01, value: 0.05 }

    costs:
        - { date: 1999-01-01, value: 10000000, currency: USD }
        - { date: 1999-10-01, value: 20000000 }
        - { date: 1999-10-05, value: 5000000, currency: USD }
        - { date: 2000-01-07, value: 100000000, currency: GBP }
        - { date: 2000-07-25, value: 5000000, currency: NOK }

    well_costs:
        - { well: OP_1, value: 10000000, currency: USD }
        - { well: OP_2, value: 20000000 }
        - { well: OP_3, value: 5000000, currency: USD }
        - { well: OP_4, value: 100000000, currency: GBP }
        - { well: OP_5, value: 1000000 }
        - { well: WI_1, value: 100000, currency: USD }
        - { well: WI_2, value: 20000000, currency: USD }
        - { well: WI_3, value: 5000000, currency: NOK }

:code:`-input` example

This argument uses output of the **drill_planner** job, or a similar output.

.. code-block:: json

    [
        {
            "name": "OP_4",
            "readydate": "2000-02-23"
        },
        {
            "name": "OP_5",
            "readydate": "2000-06-14"
        },
        {
            "name": "OP_1",
            "readydate": "2000-07-19"
        }
    ]
"""


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
            "-c/--config argument file key 'well_cost' and -i/--input argument file "
            "must always be paired; one of the two is missing."
        )

    if args and "-o" not in args and "--output" not in args:
        logger.warning(
            "Objective names ending in '_0' have been deprecated by everest! "
            "Replace objective `npv_0` with `npv` in the everest config file."
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
