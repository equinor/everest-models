import argparse
from functools import partial
from typing import Iterable

from spinningjenny.jobs.shared.arguments import (
    SchemaAction,
    bootstrap_parser,
    get_parser,
)
from spinningjenny.jobs.shared.validators import (
    parse_file,
    validate_eclipse_path_argparse,
)

from .models.config import ConfigSchema

CONFIG_ARG_KEY = ["--config", "-c"]
ECLIPSE_FILES_ARG_KEY = ["--eclipse-model", "-E"]


def _join_argument_key(key: Iterable[str]) -> str:
    return "/".join(key)


@bootstrap_parser
def build_argument_parser() -> argparse.ArgumentParser:
    SchemaAction.register_single_model(
        _join_argument_key(CONFIG_ARG_KEY),
        ConfigSchema,
    )
    parser, required_group = get_parser(
        description="""
        Design a well trajectory.
        """
    )
    required_group.add_argument(
        *CONFIG_ARG_KEY,
        required=True,
        type=partial(parse_file, schema=ConfigSchema),
        help="forward model configuration file.",
    )
    parser.add_argument(
        *ECLIPSE_FILES_ARG_KEY,
        type=validate_eclipse_path_argparse,
        help="Path to Eclipse model: '/path/to/model'; extension not needed",
    )

    return parser
