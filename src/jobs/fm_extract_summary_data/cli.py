import logging

from jobs.fm_extract_summary_data.parser import args_parser
from jobs.fm_extract_summary_data.utils import (
    apply_calculation,
    extract_value,
    validate_arguments,
    write_result,
)

logger = logging.getLogger(__name__)


def main_entry_point(args=None):
    options = args_parser.parse_args(args)
    validate_arguments(options, args_parser)

    if options.start_date:
        result = apply_calculation(
            summary=options.summary,
            calc_type=options.type,
            key=options.key,
            start_date=options.start_date,
            end_date=options.end_date,
        )
    else:
        result = extract_value(options.summary, options.key, options.end_date)

    write_result(options.output, result, options.multiplier)


if __name__ == "__main__":
    main_entry_point()
