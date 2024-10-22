import logging

from everest_models.jobs.fm_schmerge.parser import build_argument_parser
from everest_models.jobs.fm_schmerge.tasks import merge_operations_onto_schedule

logger = logging.getLogger(__name__)

FULL_JOB_NAME = "Schedule merge"


def main_entry_point(args=None):
    args_parser = build_argument_parser()
    options = args_parser.parse_args(args)

    if options.lint:
        args_parser.exit()

    schedule = merge_operations_onto_schedule(
        options.input.dated_operations(), options.schedule
    )
    options.output.write_text(schedule)
