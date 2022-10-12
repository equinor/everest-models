import logging

from jobs.fm_well_filter.parser import args_parser
from jobs.fm_well_filter.tasks import filter_wells, write_results

logger = logging.getLogger(__name__)


def main_entry_point(args=None):
    options = args_parser.parse_args(args)

    filtered_wells = filter_wells(
        wells=options.input,
        parser=args_parser,
        keep_wells=options.keep,
        remove_wells=options.remove,
    )

    write_results(filtered_wells, options.output)


if __name__ == "__main__":
    main_entry_point()
