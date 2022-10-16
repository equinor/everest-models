#!/usr/bin/env python
import errno
import logging
import sys

from spinningjenny.jobs.fm_rf.parser import args_parser
from spinningjenny.jobs.fm_rf.tasks import recovery_factor

logger = logging.getLogger(__name__)


def write_results(rf, fname):
    try:
        with open(fname, "w") as f:
            f.write("{0:.6f}".format(rf))
    except IOError as x:
        if x.errno == errno.ENOENT:
            logger.error(
                "Can not write to file - directory does not exist: {}".format(fname)
            )
        elif x.errno == errno.EACCES:
            logger.error("Can not write to file - no access: {}".format(fname))
        else:
            logger.error("Can not write to file: {}".format(fname))
        sys.exit(1)


def main_entry_point(args=None):
    args = args_parser.parse_args(args)
    logger.info("Initializing recovery factor calculation")

    rf = recovery_factor(
        ecl_sum=args.summary,
        production_key=args.production_key,
        total_volume_key=args.total_volume_key,
        start_date=args.start_date,
        end_date=args.end_date,
    )

    logger.info("Calculated recovery factor: {0:.6f}".format(rf))

    if args.output:
        logger.info("Writing results to {}".format(args.output))
        write_results(rf, args.output)


if __name__ == "__main__":
    main_entry_point()
