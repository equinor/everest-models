import argparse
from functools import partial

from everest_models.jobs.shared.arguments import (
    SchemaAction,
    bootstrap_parser,
    get_parser,
)
from everest_models.jobs.shared.validators import (
    parse_file,
    validate_eclipse_path_argparse,
)

from .models.config import ConfigSchema

CONFIG_ARG_KEY = "-c/--config"
ECLIPSE_FILES_ARG_KEY = "-E/--eclipse-model"

SCHEMAS = {CONFIG_ARG_KEY: ConfigSchema}


@bootstrap_parser
def build_argument_parser() -> argparse.ArgumentParser:
    SchemaAction.register_models(SCHEMAS)
    parser, required_group = get_parser(description="Design a well trajectory.")
    required_group.add_argument(
        *CONFIG_ARG_KEY.split("/"),
        required=True,
        type=partial(parse_file, schema=ConfigSchema),
        help="forward model configuration file.",
    )
    parser.add_argument(
        *ECLIPSE_FILES_ARG_KEY.split("/"),
        type=validate_eclipse_path_argparse,
        help="Path to Eclipse model: '/path/to/model'; extension not needed",
    )

    return parser
