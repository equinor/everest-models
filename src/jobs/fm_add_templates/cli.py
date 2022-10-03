#!/usr/bin/env python
import argparse
import json
import logging
from functools import partial

from jobs.fm_add_templates import tasks
from jobs.fm_add_templates.schemas import build_schema
from jobs.utils.io_utils import write_json_to_file
from jobs.utils.validators import is_writable, valid_config, valid_file

logger = logging.getLogger(__name__)


def _build_argument_parser():
    description = (
        "Inserts template file paths for all well operations in the "
        " given input file where the config keys match the operation"
        " information. If key sets associated with multiple template files match"
        " a well operation the template with the most keys matching will be the one"
        " inserted"
    )
    parser = argparse.ArgumentParser(description=description)

    parser.add_argument(
        "-c",
        "--config",
        type=partial(valid_config, schema=build_schema(), parser=parser),
        required=True,
        help="Config file containing list of template file paths to be injected.",
    )
    parser.add_argument(
        "-i",
        "--input",
        type=partial(valid_file, parser=parser),
        required=True,
        help="Input file that requires template paths. Json file expected ex: wells.json",
    )
    parser.add_argument(
        "-o",
        "--output",
        required=True,
        type=partial(is_writable, parser=parser),
        help="Output file",
    )

    return parser


def main_entry_point(args=None):
    arg_parser = _build_argument_parser()
    options = arg_parser.parse_args(args)

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
        arg_parser.error("\n".join(errors))

    # Write insertion result to file
    write_json_to_file(output, options.output)


if __name__ == "__main__":
    main_entry_point()
