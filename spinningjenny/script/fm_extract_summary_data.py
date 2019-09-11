import argparse

from functools import partial

from spinningjenny.extract_summary_data import (
    valid_percentile,
    validate_arguments,
    apply_calculation,
    write_result,
    extract_value,
    CalculationType,
)

from spinningjenny import valid_date, valid_ecl_file


def build_argument_parser():
    description = (
        "Module to extract Eclipse Summary keyword data (either cummulative or averaged rate)"
        " over a timeframe."
    )
    parser = argparse.ArgumentParser(description=description)

    parser.add_argument(
        "-s",
        "--summary",
        type=partial(valid_ecl_file, parser=parser),
        required=True,
        help="Eclipse summary file",
    )
    parser.add_argument(
        "-sd",
        "--start-date",
        type=partial(valid_date, parser=parser),
        help="Start date, if not specified the module will write to the output "
        "file a single summary key value for the specified end date",
    )
    parser.add_argument(
        "-ed",
        "--end-date",
        "--date",
        type=partial(valid_date, parser=parser),
        required=True,
        help="End date for the summary key interval or date for which to "
        "extract a summary key value",
    )
    parser.add_argument(
        "-k", "--key", type=str, required=True, help="Eclipse summary key"
    )
    parser.add_argument(
        "-t",
        "--type",
        type=str,
        default="max",
        choices=CalculationType.types(),
        help="Type of range calculation to use one of (max, mean, median, percentile, cummulative)",
    )
    parser.add_argument(
        "-p",
        "--percentile",
        type=partial(valid_percentile, parser=parser),
        default=95,
        help="Percentile to use when the the calculation type is also percentile. If given needs to be in the interval [0, 100]",
    )
    parser.add_argument(
        "-m", "--multiplier", type=float, default=1, help="Result multiplier"
    )
    parser.add_argument("-o", "--output", required=True, help="Output file")

    return parser


def main_entry_point(args=None):
    parser = build_argument_parser()
    options = parser.parse_args(args)
    validate_arguments(options, parser)

    if options.start_date:
        result = apply_calculation(options)
    else:
        result = extract_value(options.summary, options.key, options.end_date)

    write_result(options.output, result, options.multiplier)


if __name__ == "__main__":
    main_entry_point()
