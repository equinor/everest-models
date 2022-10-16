#!/usr/bin/env python
import logging
import os
import sys

from spinningjenny.jobs.fm_strip_dates import tasks
from spinningjenny.jobs.fm_strip_dates.parser import args_parser

logger = logging.getLogger(__name__)


def main_entry_point(args=None):
    options = args_parser.parse_args(args)

    if not os.path.exists(options.summary):
        logger.error("No such file or directory: {}".format(options.summary))

    try:
        tasks.strip_dates(
            summary_file=options.summary,
            dates=tasks.process_dates(options.dates),
            allow_missing_dates=options.allow_missing_dates,
        )
    except RuntimeError as err:
        logger.error(str(err))
        sys.exit(1)


if __name__ == "__main__":
    main_entry_point()
