import argparse
from functools import partial

from spinningjenny.jobs.fm_add_templates.schemas import build_schema
from spinningjenny.jobs.shared.validators import is_writable, valid_config, valid_file


def build_argument_parser():
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


args_parser = build_argument_parser()
