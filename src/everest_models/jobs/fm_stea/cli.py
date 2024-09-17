#!/usr/bin/env python

import logging

import stea

from everest_models.jobs.fm_stea.parser import args_parser

logger = logging.getLogger(__name__)


def main_entry_point(args=None):
    options = args_parser.parse_args(args)

    if options.lint:
        args_parser.exit()

    for res, value in (
        stea.calculate(options.config).results(stea.SteaKeys.CORPORATE).items()
    ):
        with open(f"{res}", "w") as ofh:
            ofh.write(f"{value}\n")


if __name__ == "__main__":
    main_entry_point()
