#!/usr/bin/env python

import sys
import argparse
import os

from spinningjenny import customized_logger
from spinningjenny.well_constraints import well_config
from spinningjenny.well_constraints import controls_config
from spinningjenny.well_constraints.well_constraint_job import (
    run_job,
    merge_dicts,
    load_yaml,
)
from spinningjenny.well_constraints.well_constraint_validate import (
    valid_job,
    valid_configuration,
)

logger = customized_logger.get_logger(__name__)


def main_entry_point(args=None):

    if args is None:
        args = sys.argv

    parser = well_constraint_parser()
    args = parser.parse_args(args[1:])

    logger.info("Initializing well constraints job")

    constraints = load_yaml(args.user_config)
    logger.info("Validating input file: {}".format(os.path.basename(args.user_config)))
    valid_user_config = valid_configuration(constraints, well_config._build_schema())

    optional_files = _filter_optional_files(args)
    optimizer_values, valid_control_files = _add_variable_files(optional_files)

    if not all([valid_user_config, valid_control_files]):
        sys.exit(1)

    if optimizer_values:
        constraints = merge_dicts(constraints, optimizer_values)

    well_dates = load_yaml(args.well_order_file)
    if not valid_job(well_dates, constraints):
        sys.exit(1)

    run_job(constraints, well_dates, args.output_file)


def _filter_optional_files(args):
    optional_files = [
        (args.rate_constraints, "rate"),
        (args.duration_constraints, "duration"),
        (args.phase_constraints, "phase"),
    ]
    return [x for x in optional_files if x[0]]


def _add_variable_files(optional_files):
    """
    Combines files with controls, and checks if they are valid input files
    :param optional_files:
    :return: combination of controls and bool with validity
    """
    variables = {}
    valid_files = []
    for opt_file, key in optional_files:
        input_dict = load_yaml(opt_file)
        logger.info("Validating input file: {}".format(os.path.basename(opt_file)))
        valid_file = valid_configuration(input_dict, controls_config._build_schema())
        valid_files.append(valid_file)
        if valid_file:
            variables = merge_dicts(variables, _inject_key_in_dict(input_dict, key))
    return variables, all(valid_files)


def _valid_file(fname):
    if not os.path.isfile(fname):
        raise AttributeError("File was not found: {}".format(fname))
    return fname


def well_constraint_parser():

    description = """
    A module that given a list of boundaries and well constraints creates a list of 
    well events. Varying phase, rate and time of each event is supported. Rate and 
    duration boundaries are given as min/max, and phase as a list of possibilities 
    to choose from. Will also support constants if boundaries are replaced by value.
    """
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "--well-order-file",
        required=True,
        type=_valid_file,
        help="""
        File containing well names and well opening times, 
        should be specified in Everest config.
        """,
    )
    parser.add_argument(
        "--user-config",
        required=True,
        type=_valid_file,
        help="""
        Configuration file with names, events and boundaries for constraints
        """,
    )
    parser.add_argument(
        "--rate-constraints",
        required=False,
        type=_valid_file,
        default=None,
        help="""
        Rate constraints file, from controls section of Everest config, 
        must be indexed format.
        """,
    )
    parser.add_argument(
        "--phase-constraints",
        required=False,
        type=_valid_file,
        default=None,
        help="""
        Phase constraints file, from controls section of Everest config, 
        must be indexed format. Values must be [0,1].
        """,
    )
    parser.add_argument(
        "--duration-constraints",
        required=False,
        type=_valid_file,
        default=None,
        help="""
        Duration constraints file, from controls section of Everest config, 
        must be indexed format.
        """,
    )
    parser.add_argument(
        "--output-file",
        required=True,
        type=str,
        help="Name of the outputfile. The format will be yaml.",
    )
    return parser


def _inject_key_in_dict(input_dict, new_key):
    """
    Replaces the optimizer value from the dict of the input .json file with
    a key/value pair, where the value is kept and expands the dict to match
    the format of the user config.
    :param input_dict: dictionary with optimization values
    :param key: the key in the key/value pair.
    :return: new dict
    """
    output_dict = {}
    for key, val in input_dict.items():
        for index in val:
            new_dict = {
                key: {
                    int(index): {new_key: {"optimizer_value": input_dict[key][index]}}
                }
            }
            output_dict = merge_dicts(output_dict, new_dict)

    return output_dict


if __name__ == "__main__":

    main_entry_point()
