import itertools
import logging

from everest_models.jobs.fm_drill_date_planner.parser import build_argument_parser

logger = logging.getLogger(__name__)

FULL_JOB_NAME = "Drill date planner"


def main_entry_point(args=None):
    args_parser = build_argument_parser()
    options = args_parser.parse_args(args)
    parser_options_conflicts = []

    if options.input and options.config.wells:
        args_parser.error("--input and config.wells are mutually exclusive!")

    if not options.input and not options.config.wells:
        args_parser.error("either --input or config.wells must be provided!")

    wells_input = options.input or options.config.wells
    well_dict = wells_input.to_dict()

    wells, other = itertools.tee(
        (well_dict.pop(name, name), value) for name, value in options.optimizer.items()
    )
    if bad_controls := tuple(name for name, _ in other if isinstance(name, str)):
        parser_options_conflicts.append(
            "Missing well in controls:\n\t" + ", ".join(bad_controls)
        )

    if well_dict:
        parser_options_conflicts.append(
            "Drill time missing for well(s):\n\t" + ", ".join(well_dict)
        )

    if parser_options_conflicts:
        args_parser.error("\n".join(parser_options_conflicts))

    if options.lint:
        args_parser.exit()

    for well, value in wells:
        well.drill_time += int(value)

    logger.info(f"Writing results to {options.output}")
    wells_input.json_dump(options.output)
