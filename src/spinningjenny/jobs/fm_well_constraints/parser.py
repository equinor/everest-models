import argparse
from functools import partial

import configsuite

from spinningjenny.jobs.fm_well_constraints.controls_config import (
    build_schema as controls_schema,
)
from spinningjenny.jobs.fm_well_constraints.well_config import (
    build_schema as config_schema,
)
from spinningjenny.jobs.shared.validators import (
    is_writable,
    valid_raw_config,
    valid_yaml_file,
)


def build_argument_parser():
    description = """
    A module that given a list of boundaries and well constraints creates a list of 
    well events. Varying phase, rate and time of each event is supported. Rate and 
    duration boundaries are given as min/max, and phase as a list of possibilities 
    to choose from. Will also support constants if boundaries are replaced by value.
    """
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "-i",
        "--input",
        required=True,
        type=partial(valid_yaml_file, parser=parser),
        help="""
        File in json format containing well names and well opening times,
        should be specified in Everest config (wells.json).
        """,
    )
    parser.add_argument(
        "-c",
        "--config",
        required=True,
        type=partial(valid_raw_config, schema=config_schema(), parser=parser),
        help="""
        Configuration file in yaml format with names, events and boundaries for
        constraints
        """
        + f"config format: \n{configsuite.docs.generate(config_schema())}",
    )
    parser.add_argument(
        "-rc",
        "--rate-constraints",
        required=False,
        type=partial(valid_raw_config, schema=controls_schema(), parser=parser),
        default=None,
        help="""
        Rate constraints file in json format, from controls section of Everest config,
        must be indexed format. Values must be in the interval [0, 1], 
        where 0 corresponds to the minimum possible rate value of the well
        the given index and 1 corresponds to the maximum possible value 
        of the well at the given index.
        """
        + f"config format: \n{configsuite.docs.generate(controls_schema())}",
    )
    parser.add_argument(
        "-pc",
        "--phase-constraints",
        required=False,
        type=partial(valid_raw_config, schema=controls_schema(), parser=parser),
        default=None,
        help="""
        Phase constraints file in json format, from controls section of Everest config,
        must be indexed format. Values must be in the interval [0,1], i.e 
        in a two phase case ["water", "gas"], any control value in the 
        interval [0, 0.5] will be attributed to "water" and any control 
        value in the interval (0.5, 1] will be attributed to "gas".
        """
        + f"config format: \n{configsuite.docs.generate(controls_schema())}",
    )
    parser.add_argument(
        "-dc",
        "--duration-constraints",
        required=False,
        type=partial(valid_raw_config, schema=controls_schema(), parser=parser),
        default=None,
        help="""
        Duration constraints file in json format, from controls section of Everest
        config, must be indexed format. Values must be in the interval [0, 1],
        where 0 corresponds to the minimum possible drill time for well,
        if given, 1 corresponds to the maximum drill time of the well if given.
        """
        + f"config format: \n{configsuite.docs.generate(controls_schema())}",
    )
    parser.add_argument(
        "-o",
        "--output",
        required=True,
        type=partial(is_writable, parser=parser),
        help="Name of the output file. The format will be yaml.",
    )
    return parser


args_parser = build_argument_parser()
