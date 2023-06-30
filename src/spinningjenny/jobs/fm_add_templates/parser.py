from functools import partial

from spinningjenny.jobs.fm_add_templates.config_model import TemplateConfig
from spinningjenny.jobs.shared.arguments import (
    SchemaAction,
    add_output_argument,
    add_wells_input_argument,
    bootstrap_parser,
)
from spinningjenny.jobs.shared.models import WellConfig
from spinningjenny.jobs.shared.validators import parse_file

SCHEMAS = {"config": TemplateConfig, "input": WellConfig}


def build_argument_parser():
    SchemaAction.register_single_model("-c/--config", TemplateConfig)
    parser, required_group = bootstrap_parser(
        description="Inserts template file paths for all well operations in the "
        " given input file where the config keys match the operation"
        " information. If key sets associated with multiple template files match"
        " a well operation the template with the most keys matching will be the one"
        " inserted"
    )
    add_wells_input_argument(
        required_group,
        schema=WellConfig,
        help="Input file that requires template paths. Json file expected ex: wells.json",
    )
    add_output_argument(required_group, help="Output file")
    required_group.add_argument(
        "-c",
        "--config",
        type=partial(parse_file, schema=TemplateConfig),
        required=True,
        help="Config file containing list of template file paths to be injected.",
    )

    return parser
