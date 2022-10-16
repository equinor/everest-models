#!/usr/bin/env python
import logging

from spinningjenny.jobs.fm_drill_date_planner import tasks
from spinningjenny.jobs.fm_drill_date_planner.parser import args_parser
from spinningjenny.jobs.utils.io_utils import write_json_to_file

logger = logging.getLogger(__name__)


def main_entry_point(args=None):
    options = args_parser.parse_args(args)

    output = tasks.drill_date_planner(
        options.input, options.optimizer, options.bounds, options.max_days
    )

    if options.output:
        logger.info("Writing results to {}".format(options.output))
        write_json_to_file(output, options.output)


if __name__ == "__main__":
    main_entry_point()
