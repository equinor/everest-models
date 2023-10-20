#!/usr/bin/env python
import logging

from everest_models.jobs.fm_strip_dates import tasks
from everest_models.jobs.fm_strip_dates.parser import args_parser

logger = logging.getLogger(__name__)


def main_entry_point(args=None):
    options = args_parser.parse_args(args)
    summary, summary_path = options.summary
    unique_dates = set(options.dates)
    if missing_dates := unique_dates - set(
        datetime.date() for datetime in summary.dates
    ):
        missing_dates_str = ", ".join(date.isoformat() for date in missing_dates)
        msg = (
            f"Missing date(s) in eclipse file {summary_path}:"
            f"\n\t{missing_dates_str}"
        )
        if options.allow_missing_dates:
            logger.warning(msg)
            options.dates = list(unique_dates - missing_dates)
        else:
            args_parser.error(f"\n{msg}")

    if options.lint:
        args_parser.exit()

    try:
        tasks.strip_dates(
            summary_path=summary_path,
            summary_dates=summary.dates,
            dates=options.dates,
        )
    except RuntimeError as err:
        logger.error(str(err))
        args_parser.exit(1, str(err))


if __name__ == "__main__":
    main_entry_point()
