#!/usr/bin/env python
import json
import logging

from spinningjenny.jobs.fm_add_templates import tasks
from spinningjenny.jobs.fm_add_templates.parser import args_parser
from spinningjenny.jobs.shared.io_utils import write_json_to_file

logger = logging.getLogger(__name__)


def main_entry_point(args=None):
    options = args_parser.parse_args(args)

    # Load input well operations file
    with open(options.input, "r") as f:
        wells = json.load(f)

    for duplicate in tasks.find_template_duplicates(options.config.snapshot.templates):
        logger.warning(
            "Found duplicate template file path {} in config file!".format(duplicate)
        )

    # Insert template paths in the input well operations structure
    output, warnings, errors = tasks.add_templates(
        options.config.snapshot.templates, wells
    )

    for warning in warnings:
        logger.warning(warning)
    if errors:
        args_parser.error("\n".join(errors))

    # Write insertion result to file
    write_json_to_file(output, options.output)


if __name__ == "__main__":
    main_entry_point()
