#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys
import stea
import os


def stea_main(args=None):
    if args is None:
        args = sys.argv

    if len(args) == 2:
        fname = args[1]
        if not os.path.isfile(fname):
            raise AttributeError("yaml file was not found: {}".format(fname))
    else:
        raise AttributeError(
            "Need yaml formatted configuration file as first commandline argument"
        )

    stea_input = stea.SteaInput([fname])
    res = stea.calculate(stea_input)
    for res, value in res.results(stea.SteaKeys.CORPORATE).items():
        with open("{}_0".format(res), "w") as ofh:
            ofh.write("{}\n".format(value))


if __name__ == "__main__":
    stea_main(sys.argv)
