#!/usr/bin/env python

import logging

import stea

from spinningjenny.jobs.fm_stea.parser import args_parser

logger = logging.getLogger(__name__)


def main_entry_point(args=None):
    options = args_parser.parse_args(args)
    stea_input = stea.SteaInput([options.config])
    res = stea.calculate(stea_input)
    for res, value in res.results(stea.SteaKeys.CORPORATE).items():
        with open("{}_0".format(res), "w") as ofh:
            ofh.write("{}\n".format(value))


if __name__ == "__main__":
    main_entry_point()
