#!/usr/bin/env python
import logging

from everest_models.jobs.fm_rf.parser import args_parser
from everest_models.jobs.fm_rf.tasks import recovery_factor

logger = logging.getLogger(__name__)


def main_entry_point(args=None):
    options = args_parser.parse_args(args)

    if options.lint:
        args_parser.exit()

    rf = recovery_factor(
        summary=options.summary,
        production_key=options.production_key,
        total_volume_key=options.total_volume_key,
        start_date=options.start_date,
        end_date=options.end_date,
    )

    logger.info(f"Calculated recovery factor: {rf:.6f}")

    if options.output:
        logger.info(f"Writing results to {options.output}")
        options.output.write_text(f"{rf:.6f}")


if __name__ == "__main__":
    main_entry_point()
