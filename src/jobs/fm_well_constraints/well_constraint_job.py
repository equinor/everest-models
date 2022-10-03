import datetime

try:
    from collections.abc import Mapping
except ImportError:
    from collections import Mapping

import logging
from copy import deepcopy

from jobs.utils.io_utils import write_json_to_file

logger = logging.getLogger(__name__)


def run_job(output_data, well_data, output_file):

    output_data = _insert_transformed_values(output_data)

    output_data = _add_dates(output_data, well_data)

    write_json_to_file(output_data, output_file)


def _find_index(val, options):
    """
    Calculates list index from a float between 0-1, representing
    the length of the list. Note that 0 gives the first element,
    1.0 gives the last element. For mid cases the function will
    "fall left", for example in a two element list, 0.5 will
    select the first element.
    :param val: float between 0.0-1.0
    :param options: list of length n
    :return: index
    """
    thresholds = [float(x + 1) / len(options) for x in range(len(options))]
    for idx, threshold in enumerate(thresholds):
        if val <= threshold:
            return idx


def _calc_list_value(options, value):
    if 0.0 <= value <= 1.0:
        return options[_find_index(value, options)]
    else:
        raise ValueError("Variable is {}, should be in range [0-1].".format(value))


def _calc_number_value(min_val, max_val, value):
    """Min/max scaling of input (optimizer) value"""
    return value * (max_val - min_val) + min_val


def _add_dates(input_data, well_dates):
    """
    Calculates dates based on well availability (readydate) and duration and
    injects operations with keyword (rate) into the well information file (ops).
    :param input_data: user config with simulator ready values calculated
    :param well_dates: well information, containing well availability date
    :return: list of dicts containing events
    """
    output_data = deepcopy(input_data)
    well_dates = deepcopy(well_dates)

    for well in well_dates:
        name = well["name"]

        if name not in output_data:
            continue

        if "ops" not in well:
            well["ops"] = []

        start_date = datetime.date.fromisoformat(well["readydate"])

        for _, event in output_data[name].items():

            event["date"] = {"value": start_date.isoformat()}

            new_dict = {k: v["value"] for k, v in event.items() if k != "duration"}

            new_dict["opname"] = "rate"
            well["ops"].append(new_dict)

            start_date += datetime.timedelta(days=event["duration"]["value"])
    return well_dates


def _calc_transformed_value(constraints):
    """
    Calculates output value from optimizer value and constraints, assumes the
    correct combination of keys are present in constraint. A correct combination
    is only options and optimizer_value, only min, max and opimizer value or just value
    :param constraints: Dict with predefined keys
    :type constraints: dict
    :raises: RunTimeError if constraints are not fully defined
    :return: Calculated value to be used in simulation
    :rtype: float
    """
    if "options" in constraints:
        return _calc_list_value(constraints["options"], constraints["optimizer_value"])

    elif "min" in constraints and "max" in constraints:
        return _calc_number_value(
            constraints["min"], constraints["max"], constraints["optimizer_value"]
        )

    elif "value" in constraints:
        return constraints["value"]

    else:
        raise RuntimeError(
            "Incorrect validation of user config and optimizer "
            "values, mismatch between constants, bounds and variables"
        )


def _insert_transformed_values(input_data):
    """
    :param input_data: dict of constraints
    :return: copy of input data with value calculated from constraints
    """
    output_data = deepcopy(input_data)

    for well, periods in output_data.items():
        msg = "Calculating simulator value for well: {}, number of events: {}"
        logger.info(msg.format(well, len(periods)))
        for index, events in periods.items():
            calculated_values = []
            for var_name, constraint in events.items():
                transformed_value = _calc_transformed_value(constraint)
                output_data = merge_dicts(
                    output_data,
                    {well: {index: {var_name: {"value": transformed_value}}}},
                )
                if constraint.get("optimizer_value", False):
                    calculated_values.append(
                        "[{}: {}]".format(var_name, transformed_value)
                    )
            logger.info(
                "Event {}: Calculated: {}".format(index, " ".join(calculated_values))
            )
    return output_data


def merge_dicts(*dictionaries):
    """
    Given any number of dictionaries will merge to a new dict. Will also merge
    nested dicts, if there are conflicting keys, precedence will go to the
    latter dicts.
    :param dictionaries: Any number of dictionaries that will be merged
    :type dictionaries: dict
    :return: merged dict of input dictionaries
    """

    def _merge_recursively(result_dict, new_dict):
        for key, value in new_dict.items():
            if isinstance(value, Mapping):
                if key not in result_dict:
                    result_dict[key] = {}
                _merge_recursively(result_dict[key], value)
            else:
                result_dict.update({key: value})

    merged_dictionary = {}
    for dictionary in dictionaries:
        if not isinstance(dictionary, Mapping):
            raise TypeError(
                "{} must be type dict, is {}".format(dictionary, type(dictionary))
            )
        else:
            _merge_recursively(merged_dictionary, dictionary)

    return merged_dictionary
