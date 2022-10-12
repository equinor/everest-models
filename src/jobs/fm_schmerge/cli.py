import logging

from jobs.fm_schmerge.parser import args_parser
from jobs.fm_schmerge.tasks import merge_schedule

logger = logging.getLogger(__name__)


def main_entry_point(args=None):
    options = args_parser.parse_args(args)

    merge_schedule(
        schedule_file=options.schedule,
        injections=options.input,
        output_file=options.output,
    )


if __name__ == "__main__":
    main_entry_point()
