import logging

from spinningjenny.jobs.fm_extract_summary_data.parser import args_parser
from spinningjenny.jobs.fm_extract_summary_data.tasks import (
    extract_value,
    validate_arguments,
)

logger = logging.getLogger(__name__)


def main_entry_point(args=None):
    options = args_parser.parse_args(args)
    validate_arguments(options)
    if options.lint:
        args_parser.exit()
    if options.start_date is None:
        logger.info(f"Extracting key {options.key} for single date {options.end_date}")

    extractor = (
        options.type.extract if options.start_date is not None else extract_value
    )
    result = extractor(
        summary=options.summary,
        key=options.key,
        start_date=options.start_date,
        end_date=options.end_date,
    )
    options.output.write_text(f"{result * options.multiplier:.10f}")


if __name__ == "__main__":
    main_entry_point()
