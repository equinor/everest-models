#!/usr/bin/env python
import argparse
import json

from functools import partial

from spinningjenny import (
    customized_logger,
    valid_file,
    valid_config,
    write_json_to_file,
    is_writable,
)
from spinningjenny.add_templates.add_templates_job import (
    add_templates,
    find_template_duplicates,
)
from spinningjenny.add_templates.add_tmpl_schema import build_schema

logger = customized_logger.get_logger(__name__)


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

    for duplicate in find_template_duplicates(options.config.snapshot.templates):
        logger.warning(
            "Found duplicate template file path {} in config file!".format(duplicate)
        )

    # Insert template paths in the input well operations structure
    output, warnings, errors = add_templates(options.config.snapshot.templates, wells)

    for warning in warnings:
        logger.warning(warning)
    if errors:
        arg_parser.error("\n".join(errors))

    # Write insertion result to file
    write_json_to_file(output, options.output)


if __name__ == "__main__":
    main_entry_point()
