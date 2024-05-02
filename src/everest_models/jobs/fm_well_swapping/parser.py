from datetime import date
from functools import partial
from typing import Dict, Tuple

from everest_models.jobs.shared.arguments import (
    Parser,
    add_output_argument,
    add_wells_input_argument,
)
from everest_models.jobs.shared.io_utils import load_json
from everest_models.jobs.shared.parsers import bootstrap_parser
from everest_models.jobs.shared.validators import (
    parse_file,
    valid_optimizer,
)

from .model_config import ConfigSchema

_CONFIG_ARGUMENT = "config"
_PRIORITIES_ARGUMENT = "-p/--priorities"
_CONSTRAINTS_ARGUMENT = "-c/--constraints"
SCHEMAS = {_CONFIG_ARGUMENT: ConfigSchema}


def _clean_constraint(value: str) -> Dict[str, Tuple[float, ...]]:
    return {key: tuple(value.values()) for key, value in load_json(value).items()}


@bootstrap_parser(
    schemas=SCHEMAS,  # type: ignore
    deprication=date(2024, 5, 1),
    prog="Well Swapping",
    description="Swap well operation status over multiple time intervals.",
)
def build_argument_parser(
    parser: Parser, legacy: bool = False, lint: bool = False
) -> None:
    parser.add_argument(
        f"{'--' if legacy else ''}{_CONFIG_ARGUMENT}",
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
    parser.add_argument(
        "--allow-reopen",
        action="store_true",
        help="ignores irreversible states if exist",
    )
    add_wells_input_argument(
        parser,
        required=False,
        arg=("-w", "--wells"),
        help="Everest generated wells.json file",
    )
    if not lint:
        add_output_argument(
            parser,
            required=False,
            help="Where to write wells opertation json file",
        )
