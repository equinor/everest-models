#!/usr/bin/env python
import argparse
import json
import yaml

from functools import partial
from configsuite import ConfigSuite

from spinningjenny import customized_logger, valid_file
from spinningjenny.add_templates.add_templates_job import (
    add_templates,
    find_template_duplicates,
)
from spinningjenny.add_templates.add_tmpl_schema import build_schema

logger = customized_logger.get_logger(__name__)


def _valid_add_template_config(path, parser):
    valid_file(path, parser)
    with open(path, "r") as f:
        dict_config = yaml.safe_load(f)

    config = ConfigSuite(dict_config, build_schema())
    if not config.valid:
        parser.error(
            "Invalid config file: {}\n{}".format(
                path, "\n".join([err.msg for err in config.errors])
            )
        )
    return config.snapshot.templates


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
        "--config",
        type=partial(_valid_add_template_config, parser=parser),
        required=True,
        help="Config file containing list of template file paths to be injected.",
    )
    parser.add_argument(
        "--input-file",
        type=partial(valid_file, parser=parser),
        required=True,
        help="Input file that requires template paths. Json file expected ex: wells.json",
    )
    parser.add_argument("--output-file", required=True, help="Output file")

    return parser


def main_entry_point(args=None):
    arg_parser = _build_argument_parser()
    options = arg_parser.parse_args(args)

    # Load input well operations file
    with open(options.input_file, "r") as f:
        wells = json.load(f)

    for duplicate in find_template_duplicates(options.config):
        logger.warning(
            "Found duplicate template file path {} in config file!".format(duplicate)
        )

    # Insert template paths in the input well operations structure
    output, warnings = add_templates(options.config, wells)

    for warning in warnings:
        logger.warning(warning)

    # Write insertion result to file
    with open(options.output_file, "w") as f:
        json.dump(output, f, indent=2, separators=(",", ": "))


if __name__ == "__main__":
    main_entry_point()
