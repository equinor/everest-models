#!/usr/bin/env python

import json
import logging
from typing import Dict, Iterable, Literal, Tuple

from .parser import args_parser


def process_properties(
    priority: Dict[str, float], status: Dict[str, Literal[-1, 0, 1]], allow_reopen: bool
) -> Iterable[Tuple[str, float]]:
    sorted_priorities = sorted(priority.items(), key=lambda x: x[1], reverse=True)
    return (
        sorted_priorities
        if allow_reopen
        else filter(lambda x: x if status[x[0]] > 0 else None, sorted_priorities)
    )


def main_entry_point(args=None):
    options = args_parser.parse_args(args)
    logging.debug(f"Initial: {options.switch}")

    for index, (key, _) in enumerate(
        process_properties(options.priority, options.switch, options.allow_reopen)
    ):
        options.switch[key] = (
            1 if index < options.number_of_injectors and options.switch[key] < 1 else -1
        )

    logging.debug(f"New: {options.switch}")
    with options.output.open("w") as fp:
        json.dump(options.switch, fp)


if __name__ == "__main__":
    main_entry_point()
