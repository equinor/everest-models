import argparse
from functools import partial

import configsuite

from jobs.fm_drill_planner import drill_planner_schema
from jobs.utils.validators import is_writable, valid_yaml_file


def build_argument_parser():
    description = """
    A module that given a well priority list and a set of constraints,
    creates a list of dates for each well to be completed.
    Any well may have multiple options as to where it can be drilled,
    both for different slots and rigs. The module will try to find the
    optimum event combinations that allows for the wells to be completed
    as quickly as possible, and at the same time make sure that the
    dates that are output will be a valid drill plan.
    """
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "-i",
        "--input",
        required=True,
        type=partial(valid_yaml_file, parser=parser),
        help="File containing information related to wells. The format is "
        "consistent with the wells.json file when running everest and can "
        "be used directly.",
    )
    parser.add_argument(
        "-c",
        "--config",
        required=True,
        type=partial(valid_yaml_file, parser=parser),
        help="""
        Configuration file in yaml format describing the constraints of the field
        development. The file must contain information about rigs and slots
        that the wells can be drilled through. Additional information, such as
        when rigs and slots are available is also added here.
        """
        + f"Schema: \n{configsuite.docs.generate(drill_planner_schema.build())}",
    )
    parser.add_argument(
        "-opt",
        "--optimizer",
        required=True,
        type=partial(valid_yaml_file, parser=parser),
        help="The optimizer file in yaml format is the file output from everest that "
        "contains the well priority values - a float for each well.",
    )
    parser.add_argument(
        "-tl",
        "--time-limit",
        required=False,
        type=int,
        default=3600,
        help="Maximum time limit for the solver in seconds."
        "If a solution has not been reached within this time, a greedy"
        "approach will be used instead.",
    )
    parser.add_argument(
        "-o",
        "--output",
        required=True,
        type=partial(is_writable, parser=parser),
        help="Name of the output-file. The output-file (json) will contain the same "
        "information as the input-file, including the results from the "
        "drill_planner. Please note that it is highly recommended to not use the "
        "same filename as the input-file. In cases where the same workflow is run "
        "twice, it is generally adviced that the input-file for each job is consistent",
    )
    parser.add_argument(
        "--ignore-end-date",
        action="store_true",
        help="Ignore the end date in the config file.",
    )
    return parser


args_parser = build_argument_parser()
