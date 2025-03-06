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
def build_argument_parser(skip_type=False) -> argparse.ArgumentParser:
    SchemaAction.register_models(SCHEMAS)
    parser, required_group = get_parser(
        prog="fm_well_trajectory",
        description="Design a well trajectory based on provided parametrized guide points."
        "The guide points are interpolated in order to obtain a smooth well trajectory."
        "Then, inputs for the reservoir simulator are created in form of completion "
        "data consisting of grid cells that trajectory interjects, well-to-cell connection "
        "factors, well diameter, skin, etc. Optionally, only perforated intervals are created "
        "for which provided perforation criteria are satisfied based on information, such as "
        "geological formation or any static or dynamic property in the grid cell of a reservoir simulation model.",
    )
    required_group.add_argument(
        *CONFIG_ARG_KEY.split("/"),
        required=True,
        type=partial(parse_file, schema=ConfigSchema) if not skip_type else str,
        help="Forward model configuration file in YAML format.",
    )
    parser.add_argument(
        *ECLIPSE_FILES_ARG_KEY.split("/"),
        type=validate_eclipse_path_argparse if not skip_type else str,
        help=(
            "Path to simulation model: '/path/to/model'; extension not required. "
            "GRID and INIT files always expected. If dynamic perforations defined in "
            "CONFIG file then UNRST file expected."
        ),
    )

    return parser
