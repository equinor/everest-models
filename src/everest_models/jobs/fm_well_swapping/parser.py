import argparse
from functools import partial
from typing import Dict, Tuple

from everest_models.jobs.shared.arguments import (
    SchemaAction,
    add_output_argument,
    add_wells_input_argument,
)
from everest_models.jobs.shared.io_utils import load_json
from everest_models.jobs.shared.validators import (
    parse_file,
    valid_optimizer,
)

from .models import ConfigSchema, Wells

_CONFIG_ARGUMENT = "config"
_PRIORITIES_ARGUMENT = "-p/--priorities"
_CONSTRAINTS_ARGUMENT = "-c/--constraints"
SCHEMAS = {_CONFIG_ARGUMENT: ConfigSchema}


def _clean_constraint(value: str) -> Dict[str, Tuple[float, ...]]:
    return {key: tuple(value.values()) for key, value in load_json(value).items()}


def add_file_arguments(
    parser: argparse.ArgumentParser, required: bool = True
) -> argparse._ArgumentGroup:
    required_group = parser.add_argument_group("required named arguments")
    parser.add_argument(
        _CONFIG_ARGUMENT,
        type=partial(parse_file, schema=ConfigSchema),
        help="well swapping configuration file",
    )
    parser.add_argument(
        *_CONSTRAINTS_ARGUMENT.split("/"),
        type=_clean_constraint,
        help="Everest generated optimized constraints",
    )
    parser.add_argument(
        *_PRIORITIES_ARGUMENT.split("/"),
        type=valid_optimizer,
        help="Everest generated optimized priorities",
    )
    add_wells_input_argument(
        required_group if required else parser,
        schema=Wells,
        required=required,
        help="Everest generated wells.json file",
    )
    return required_group


def build_argument_parser() -> argparse.ArgumentParser:
    SchemaAction.register_models(SCHEMAS)
    parser = argparse.ArgumentParser(prog="Well Swapping", description="we swap wells")
    sub_parser = parser.add_subparsers()
    run = sub_parser.add_parser("run", help="run well swapping forward model")
    add_output_argument(
        add_file_arguments(run), help="Where do you wish to write this run too?"
    )
    run.add_argument(
        "--allow-reopen",
        action="store_true",
        help="ignores irreversible states if exist",
    )
    schema = sub_parser.add_parser("schema", help="input files schematic specification")
    schema.add_argument(
        "--show",
        nargs=0,
        action=SchemaAction,
        help="write all user defined input file schematics to stdout",
    )
    schema.add_argument(
        "--init",
        nargs=0,
        action=SchemaAction,
        help="Initialize all needed configuration files",
    )
    add_file_arguments(
        parser=sub_parser.add_parser(
            "parse", help="parse all files that would be used under run"
        ),
        required=False,
    )
    return parser
