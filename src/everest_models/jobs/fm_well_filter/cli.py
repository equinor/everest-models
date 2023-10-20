import logging

from everest_models.jobs.fm_well_filter.parser import build_argument_parser

logger = logging.getLogger(__name__)


def main_entry_point(args=None):
    args_parser = build_argument_parser()
    options = args_parser.parse_args(args)
    keep = options.remove is None
    well_names = set(options.remove or options.keep)

    if diff := well_names.difference(well.name for well in options.input):
        logger.warning(
            f"{'Keep' if keep else 'Remove'} value(s) are not present in input file:\n\t"
            + ", ".join(diff)
        )

    if options.lint:
        args_parser.exit()

    options.input.set_wells(
        filter(
            lambda x: x.name in well_names if keep else x.name not in well_names,
            options.input,
        )
    )

    options.input.json_dump(options.output)


if __name__ == "__main__":
    main_entry_point()
