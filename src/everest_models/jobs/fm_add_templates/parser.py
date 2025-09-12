from functools import partial

from everest_models.jobs.fm_add_templates.config_model import TemplateConfig
from everest_models.jobs.shared.arguments import (
    SchemaAction,
    add_output_argument,
    add_wells_input_argument,
    bootstrap_parser,
    get_parser,
)
from everest_models.jobs.shared.models import Wells
from everest_models.jobs.shared.validators import parse_file

_CONFIG_ARGUMENT = "-c/--config"
SCHEMAS = {_CONFIG_ARGUMENT: TemplateConfig}


@bootstrap_parser
def build_argument_parser(skip_type=False):
    SchemaAction.register_models(SCHEMAS)
    parser, required_group = get_parser(
        description="Inserts template file paths for all well operations in the "
        " given input file where the config keys match the operation"
        " information. If key sets associated with multiple template files match"
        " a well operation the template with the most keys matching will be the one"
        " inserted"
    )
    add_wells_input_argument(
        parser,
        schema=Wells,
        help="Input file that requires template paths. Json file expected ex: wells.json",
        skip_type=skip_type,
        required=False,
    )
    add_output_argument(required_group, help="Output file", skip_type=skip_type)
    required_group.add_argument(
        *_CONFIG_ARGUMENT.split("/"),
        type=partial(parse_file, schema=TemplateConfig) if not skip_type else str,
        required=True,
        help="Config file containing list of template file paths to be injected.",
    )

    return parser
