#!/usr/bin/env python

from .parser import args_parser


def main_entry_point(args=None):
    options = args_parser.parse_args(args)

    for well in options.input:
        if index := options.switch.get(well.name):
            well.ops[0].opname = options.switch_dict[str(index)]

    options.input.json_dump(options.output)


if __name__ == "__main__":
    main_entry_point()
