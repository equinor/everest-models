from functools import partial

from everest_models.jobs.fm_add_templates.config_model import TemplateConfig
from everest_models.jobs.shared.arguments import (
    SchemaAction,
    add_output_argument,
    add_wells_input_argument,
    bootstrap_parser,
    get_parser,
)
from everest_models.jobs.shared.models import WellConfig
from everest_models.jobs.shared.validators import parse_file

SCHEMAS = {"config": TemplateConfig, "input": WellConfig}


@bootstrap_parser
def build_argument_parser():
    SchemaAction.register_single_model("-c/--config", TemplateConfig)
    parser, required_group = get_parser(
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
