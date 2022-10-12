#!/usr/bin/env python

import logging
import sys

from jobs.fm_well_constraints.parser import args_parser
from jobs.fm_well_constraints.well_constraint_job import merge_dicts, run_job
from jobs.fm_well_constraints.well_constraint_validate import valid_job

logger = logging.getLogger(__name__)


def main_entry_point(args=None):
    options = args_parser.parse_args(args)

    logger.info("Initializing well constraints job")

    constraints = options.config

    optional_files = _filter_optional_files(options)
    optimizer_values = _add_variable_files(optional_files)

    if optimizer_values:
        constraints = merge_dicts(constraints, optimizer_values)

    well_dates = options.input
    if not valid_job(well_dates, constraints):
        sys.exit(1)

    run_job(constraints, well_dates, options.output)


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
    for opt_constraint, key in optional_files:
        variables = merge_dicts(variables, _inject_key_in_dict(opt_constraint, key))
    return variables


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
