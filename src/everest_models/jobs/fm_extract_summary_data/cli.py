import logging

from everest_models.jobs.fm_extract_summary_data.parser import (
    args_parser,
    load_static_config,
)
from everest_models.jobs.fm_extract_summary_data.tasks import (
    CalculationType,
    extract_static_targets,
    extract_value,
    extract_vector_value,
    validate_arguments,
    write_static_targets,
)

logger = logging.getLogger(__name__)

FULL_JOB_NAME = "Extract summary data"


def main_entry_point(args=None):
    options = args_parser.parse_args(args)

    if options.config:
        if not options.summary:
            args_parser.error("--summary is required with --config")
        if any(
            (
                options.output,
                options.key,
                options.aggregation,
                options.output_date,
                options.diff,
            )
        ):
            args_parser.error(
                "--config cannot be combined with --output, --key, --aggregation, "
                "--output-date, or --diff"
            )
        config = load_static_config(options.config)
        if options.lint:
            args_parser.exit()
        report_dates = [date.date() for date in options.summary.dates]
        if options.end_date is None:
            options.end_date = report_dates[-1]
        if options.start_date is not None and options.start_date > options.end_date:
            args_parser.error("--start-date cannot be after --end-date")
        if options.start_date is not None and options.start_date not in report_dates:
            args_parser.error("--start-date is not a summary report date")
        if options.end_date not in report_dates:
            args_parser.error("--end-date is not a summary report date")
        write_static_targets(
            extract_static_targets(
                options.summary, config, options.start_date, options.end_date
            )
        )
        return

    if not options.summary or not options.output or not options.key:
        args_parser.error(
            "--summary, --output, and --key are required without --config"
        )
    if options.aggregation is not None and options.output_date is not None:
        args_parser.error("--aggregation cannot be combined with --output-date")
    if options.diff and (
        options.aggregation is not None or options.output_date is not None
    ):
        args_parser.error(
            "--diff cannot be combined with --aggregation or --output-date"
        )
    if options.diff and options.start_date is None:
        args_parser.error("--diff requires --start-date")
    if options.output_date is not None and (
        options.start_date is not None or options.end_date is not None
    ):
        args_parser.error(
            "--output-date cannot be combined with --start-date or --end-date"
        )
    if options.unit_conversion == 0:
        args_parser.error("--unit-conversion must be non-zero")
    validate_arguments(options)
    if options.lint:
        args_parser.exit()
    if options.output_date is not None:
        logger.info(
            f"Extracting key {options.key} for single date {options.output_date}"
        )
    elif options.start_date is None:
        logger.info(f"Extracting key {options.key} for single date {options.end_date}")

    if options.output_date is not None:
        result = extract_vector_value(
            options.summary,
            options.key,
            output_date=options.output_date,
        )[0]
    elif options.aggregation is not None:
        result = extract_vector_value(
            options.summary,
            options.key,
            aggregation=options.aggregation,
            start_date=options.start_date,
            end_date=options.end_date,
        )[0]
    elif options.diff:
        result = CalculationType.DIFF.extract(
            options.summary,
            options.key,
            options.start_date,
            options.end_date,
        )
    else:
        result = extract_value(
            summary=options.summary,
            key=options.key,
            end_date=options.end_date,
        )
    options.output.write_text(f"{result / options.unit_conversion:.10f}")
