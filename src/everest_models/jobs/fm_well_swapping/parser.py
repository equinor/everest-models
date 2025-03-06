from functools import partial
from typing import Dict, Tuple

from everest_models.jobs.shared.parsers.action import SchemaAction

from ..shared.arguments import (
    Parser,
    add_output_argument,
    add_wells_input_argument,
    bootstrap_parser,
    get_parser,
)
from ..shared.io_utils import load_json
from ..shared.validators import (
    is_gt_zero,
    parse_file,
    valid_optimizer,
)
from .models import ConfigSchema

_CONFIG_ARGUMENT = "-c/--config"
_PRIORITIES_ARGUMENT = "-p/--priorities"
_CONSTRAINTS_ARGUMENT = "-cr/--constraints"
_LIMIT_ARGUMENT = "-il/--iteration-limit"

SCHEMAS = {_CONFIG_ARGUMENT: ConfigSchema}


def _clean_constraint(value: str) -> Dict[str, Tuple[float, ...]]:
    return {key: tuple(value.values()) for key, value in load_json(value).items()}


@bootstrap_parser
def build_argument_parser(lint: bool = False, **kwargs) -> Parser:
    skip_type = kwargs.pop("skip_type", False)
    SchemaAction.register_models(SCHEMAS)

    parser, required_group = get_parser(
        prog="fm_well_swapping",
        description=(
            "Swaps well operation state over multiple time intervals according "
            "to multiple sets of priority values, state quota constraints and "
            "allowed state changing actions."
        ),
    )

    required_group.add_argument(
        *_CONFIG_ARGUMENT.split("/"),
        required=True,
        type=partial(parse_file, schema=ConfigSchema) if not skip_type else str,
        help=(
            "Configuration file containing additional information defining allowed swapping "
            "actions, quotas and starting time to determine the swapping schedule."
        ),
    )
    parser.add_argument(
        *_CONSTRAINTS_ARGUMENT.split("/"),
        type=_clean_constraint if not skip_type else str,
        help="EVEREST-generated JSON file containing the values defining each swapping time interval to be optimized",
    )
    parser.add_argument(
        *_PRIORITIES_ARGUMENT.split("/"),
        type=valid_optimizer if not skip_type else str,
        help="EVEREST-generated JSON file containing the sets of priority values to be optimized",
    )
    parser.add_argument(
        *_LIMIT_ARGUMENT.split("/"),
        default=0,
        type=partial(
            is_gt_zero, msg="limit-number-iterations must be a positive number"
        ),
        help="Limit the number of iteration, this value is capped by available iterations.",
    )
    add_wells_input_argument(
        parser,
        required=False,
        arg=("-cs", "--cases"),
        help="EVEREST-generated wells.json file",
        skip_type=skip_type,
    )
    if not lint:
        add_output_argument(
            parser,
            required=False,
            help="Path to generated output JSON file",
            skip_type=skip_type,
        )
    return parser
