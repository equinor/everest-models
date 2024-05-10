from datetime import date
from functools import partial
from typing import Dict, Tuple

from ..shared.arguments import (
    Parser,
    add_output_argument,
    add_wells_input_argument,
)
from ..shared.io_utils import load_json
from ..shared.parsers import bootstrap_parser
from ..shared.validators import (
    is_gt_zero,
    parse_file,
    valid_optimizer,
)
from .models import ConfigSchema

_CONFIG_ARGUMENT = "config"
_PRIORITIES_ARGUMENT = "-p/--priorities"
_CONSTRAINTS_ARGUMENT = "-c/--constraints"
SCHEMAS = {_CONFIG_ARGUMENT: ConfigSchema}


def _clean_constraint(value: str) -> Dict[str, Tuple[float, ...]]:
    return {key: tuple(value.values()) for key, value in load_json(value).items()}


# TODO: Change program name to state adjuster or something more related to what it does
# omit anything to do with well
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
        "-il",
        "--iteration-limit",
        default=0,
        type=partial(is_gt_zero, "limit-number-iterations must be a positive number"),
        help="Limit the number of iteration, this value is capped by available iterations.",
    )
    add_wells_input_argument(
        parser,
        required=False,
        arg=("-cs", "--cases"),
        help="Everest generated wells.json file",
    )
    if not lint:
        add_output_argument(
            parser,
            required=False,
            help="Where to write output file to",
        )
