#!/usr/bin/env python

import sys
import stea
import argparse


def _get_args_parser():
    description = (
        "STEA is a powerful economic analysis tool used for complex economic"
        "analysis and portfolio optimization. STEA helps you analyze single"
        "projects, large and small portfolios and complex decision trees."
        "As output, for each of the entries in the result section of the"
        "yaml config file, STEA will create result files"
        "ex: Res1_0, Res2_0, .. Res#_0"
    )
    parser = argparse.ArgumentParser(description=description)

    parser.add_argument("config", help="STEA config file, yaml format required")
    return parser


def stea_main(args=None):
    if args is None:
        args = sys.argv

    parser = _get_args_parser()
    options = parser.parse_args(args[1:])
    stea_input = stea.SteaInput([options.config])
    res = stea.calculate(stea_input)
    for res, value in res.results(stea.SteaKeys.CORPORATE).items():
        with open("{}_0".format(res), "w") as ofh:
            ofh.write("{}\n".format(value))


if __name__ == "__main__":
    stea_main(sys.argv)
