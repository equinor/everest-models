#!/usr/bin/env python
import os
import argparse
import re
import shutil

from ecl.eclfile import EclFile, FortIO


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


def strip_sum(summary_file, dates_file):
    with open(dates_file) as f:
        datelist = [
            (int(date_match[0]), int(date_match[1]), int(date_match[2]))
            for date_match in re.findall('(\d+)\.(\d+)\.(\d+)', f.read())
        ]

    filename, file_extension = os.path.splitext(summary_file)
    tmp_file_path = filename + "_tmp." + file_extension
    shutil.move(summary_file, tmp_file_path)
    shutil.copy(filename + ".SMSPEC", filename + "_tmp.SMSPEC")

    ecl_file = EclFile(tmp_file_path)
    fort_io = FortIO(summary_file, mode=2)

    valid_date = True
    for kw in ecl_file:
        (tmptype, _, _) = kw.header

        if tmptype == "PARAMS":
            valid_date = (kw[2], kw[3], kw[4]) in datelist
        if tmptype != "SEQHDR" or valid_date:
            kw.fwrite(fort_io)

    ecl_file.close()
    fort_io.close()


if __name__ == '__main__':
    arg_parser = _build_argument_parser()
    args = arg_parser.parse_args()
    strip_sum(
        summary_file=args.summary,
        dates_file=args.dates
    )
