import logging

from spinningjenny.jobs.fm_interpret_well_drill import tasks
from spinningjenny.jobs.fm_interpret_well_drill.parser import args_parser

logger = logging.getLogger(__name__)


def main_entry_point(args=None):
    options = args_parser.parse_args(args)

    tasks.interpret_well_drill(
        dakota_values_file=options.input, output_file=options.output
    )


if __name__ == "__main__":
    main_entry_point()
