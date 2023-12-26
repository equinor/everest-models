#!/usr/bin/env python

import itertools

from everest_models.jobs.shared.models import WellConfig

from .parser import args_parser


def main_entry_point(args=None):
    options = args_parser.parse_args(args)
    wells = tuple(itertools.chain.from_iterable(options.input))
    for index, well in enumerate(wells):
        date = options.dates[index]["readydate"]
        well.readydate = date
        well.completion_date = date
        well.ops[0].date = date
    WellConfig.parse_obj(wells).json_dump(options.output)


if __name__ == "__main__":
    main_entry_point()
