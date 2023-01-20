import logging

from spinningjenny.jobs.fm_schmerge.parser import build_argument_parser
from spinningjenny.jobs.fm_schmerge.tasks import ScheduleInserter

logger = logging.getLogger(__name__)


def main_entry_point(args=None):
    args_parser = build_argument_parser()
    options = args_parser.parse_args(args)

    if options.lint:
        args_parser.exit()

    inserter = ScheduleInserter(options.schedule)
    inserter.insert_operations(options.input.dated_operations())

    options.output.write_text(inserter.schedule)


if __name__ == "__main__":
    main_entry_point()
