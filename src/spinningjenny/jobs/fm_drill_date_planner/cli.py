#!/usr/bin/env python
import itertools
import logging

from spinningjenny.jobs.fm_drill_date_planner.parser import build_argument_parser
from spinningjenny.jobs.shared.converters import rescale_value

logger = logging.getLogger(__name__)


def main_entry_point(args=None):
    args_parser = build_argument_parser()
    options = args_parser.parse_args(args)
    parser_options_conflicts = []
    well_dict = options.input.to_dict()

    if options.bounds[1] < options.bounds[0]:
        parser_options_conflicts.append(
            f"Invalid bounds: lower bound greater than upper, {options.bounds}"
        )

    wells, other = itertools.tee(
        (well_dict.pop(name, name), value) for name, value in options.optimizer.items()
    )
    if bad_controls := tuple(name for name, _ in other if isinstance(name, str)):
        parser_options_conflicts.append(
            "Missing well in controls:\n\t" + ", ".join(bad_controls)
        )

    if well_dict:
        parser_options_conflicts.append(
            "Drill time missing for well(s):\n\t" + ", ".join(well_dict)
        )

    if parser_options_conflicts:
        args_parser.error("\n".join(parser_options_conflicts))

    if options.lint:
        args_parser.exit()

    for well, value in wells:
        well.drill_time += rescale_value(
            value, options.bounds[0], options.bounds[1], 0, options.max_days
        )

    logger.info(f"Writing results to {options.output}")
    options.input.json_dump(options.output)


if __name__ == "__main__":
    main_entry_point()
