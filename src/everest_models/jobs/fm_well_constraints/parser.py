import argparse
from functools import partial

from everest_models.jobs.fm_well_constraints.models import (
    Constraints,
    WellConstraintConfig,
)
from everest_models.jobs.shared.arguments import (
    SchemaAction,
    add_file_schemas,
    add_lint_argument,
    add_output_argument,
    add_wells_input_argument,
    get_parser,
    parse_file,
)
from everest_models.jobs.shared.models.wells import WellConfig

CONFIG_ARG_KEY = "-c/--config"
RATE_CONSTRAINTS_ARG_KEY = "-rc/--rate-constraints"
PHASE_CONSTRAINTS_ARG_KEY = "-pc/--phase-constraints"
DURATION_CONSTRAINTS_ARG_KEY = "-dc/--duration-constraints"

SCHEMAS = {
    CONFIG_ARG_KEY: WellConstraintConfig,
    RATE_CONSTRAINTS_ARG_KEY: Constraints,
    PHASE_CONSTRAINTS_ARG_KEY: Constraints,
    DURATION_CONSTRAINTS_ARG_KEY: Constraints,
}

constraint_parameters = dict(default=None, type=partial(parse_file, schema=Constraints))


def build_argument_parser() -> argparse.ArgumentParser:
    SchemaAction.register_models(SCHEMAS)
    parser, required_group = get_parser(
        description="""
        A module that given a list of boundaries and well constraints creates a list of 
        well events. Varying phase, rate and time of each event is supported. Rate and 
        duration boundaries are given as min/max, and phase as a list of possibilities 
        to choose from. Also support constants if boundaries are replaced by value.
        """
    )
    add_wells_input_argument(
        required_group,
        schema=WellConfig,
        help="""
        File in json format containing well names and well opening times,
        should be specified in Everest config (wells.json).
        """,
    )
    add_file_schemas(parser)
    add_lint_argument(parser)
    add_output_argument(
        required_group,
        help="Name of the output file. The format will be yaml.",
    )
    required_group.add_argument(
        *CONFIG_ARG_KEY.split("/"),
        required=True,
        type=partial(parse_file, schema=WellConstraintConfig),
        help="""
        Configuration file in yaml format with names, events and boundaries for
        constraints
        """,
    )
    parser.add_argument(
        *RATE_CONSTRAINTS_ARG_KEY.split("/"),
        help="""
        Rate constraints file in json format, from controls section of Everest config,
        must be indexed format. Values must be in the interval [0, 1],
        where 0 corresponds to the minimum possible rate value of the well
        the given index and 1 corresponds to the maximum possible value
        of the well at the given index.
        """,
        **constraint_parameters,
    )
    parser.add_argument(
        *PHASE_CONSTRAINTS_ARG_KEY.split("/"),
        help="""
        Phase constraints file in json format, from controls section of Everest config,
        must be indexed format. Values must be in the interval [0,1], i.e
        in a two phase case ["water", "gas"], any control value in the
        interval [0, 0.5] will be attributed to "water" and any control
        value in the interval (0.5, 1] will be attributed to "gas".
        """,
        **constraint_parameters,
    )
    parser.add_argument(
        *DURATION_CONSTRAINTS_ARG_KEY.split("/"),
        help="""
        Duration constraints file in json format, from controls section of Everest
        config, must be indexed format. Values must be in the interval [0, 1],
        where 0 corresponds to the minimum possible drill time for well,
        if given, 1 corresponds to the maximum drill time of the well if given.
        """,
        **constraint_parameters,
    )
    return parser
