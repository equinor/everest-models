#!/usr/bin/env python
import argparse
from spinningjenny.strip_sum_job import strip_sum


def _build_argument_parser():
    description = (
        'The strip_sum job makes sure the summary file contains only report'
        ' steps at the dates specified in the dates file'
    )
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
            '--summary',
            required=True,
            help='Ecl summary file',
            )
    parser.add_argument(
            '--dates',
            required=True,
            help='File containing date in the format dd/mm/yyyy',
            )
    return parser


if __name__ == '__main__':
    arg_parser = _build_argument_parser()
    args = arg_parser.parse_args()
    strip_sum(
        summary_file=args.summary,
        dates_file=args.dates
    )
