import json
import logging

from everest_models.jobs.fm_interpret_well_drill.parser import args_parser

logger = logging.getLogger(__name__)

FULL_JOB_NAME = "Interpret well drill"


def main_entry_point(args=None):
    options = args_parser.parse_args(args)
    if not all(type(value) in (float, int) for value in options.input.values()):
        args_parser.error(
            "-i/--input file, Make sure all values in 'key: value' pairs are valid numbers."
        )

    if options.lint:
        args_parser.exit()

    with options.output.open("w", encoding="utf-8") as fp:
        json.dump([well for well, value in options.input.items() if value >= 0.5], fp)


if __name__ == "__main__":
    main_entry_point()
