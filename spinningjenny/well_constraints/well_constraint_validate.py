import logging
import os

import configsuite

logger = logging.getLogger(__name__)


def valid_job(well_dates, constraints):
    """
    Linting to check if the job is valid,
    will log errors and return result of validation.
    :param well_dates: Well information file with names and readydates
    :type well_dates: list
    :param constraints: Dict of dicts with optimizer key/value and constraint key/value
    :type constraints: dict
    :return: Result of input configuration validation
    :rtype: bool
    """
    logger.info("Validating configuration")
    time_errors = _validate_time(well_dates, constraints.keys())

    if time_errors:
        logger.error("Missing start date errors:")
        for error in time_errors:
            logger.error(error)

    constraint_errors, value_errors = _validate_constraints(constraints)
    if constraint_errors:
        msg = "The following should only have optimizer_value and bounds (variable) or just value (constant):"
        logger.error(msg)
        for error in constraint_errors:
            logger.error(error)

    if value_errors:
        logger.error("Min/max bounds errors:")
        for error in value_errors:
            logger.error(error)

    if time_errors or constraint_errors or value_errors:
        logger.error(
            "Invalid configuration, number of errors: {}".format(
                len(time_errors) + len(constraint_errors) + len(value_errors)
            )
        )
        return False
    logger.info("Valid configuration")
    return True


def valid_configuration(input_data, schema):
    """
    Creates a ConfigSuite instance and validates the configuration
    :param input_data: configuration dictionary
    :type input_data: dict
    :param schema: configsuite schema
    :type schema: dict
    :returns: configsuite config validity
    :rtype: bool
    """
    config = configsuite.ConfigSuite(input_data, schema, deduce_required=True)

    if not config.valid:
        for error in config.errors:
            logger.error(error)
        return False

    return True


def _valid_event(event):
    """
    Checks that optimizer_values are injected in an event where there are constraints
    :param event: Dict of event constraints
    :type event: dict
    :return: Only correct keys present
    :rtype: bool
    """
    has_min_max = set(event) == {"optimizer_value", "min", "max"}
    has_options = set(event) == {"optimizer_value", "options"}
    has_value = set(event) == {"value"}
    if has_options:
        return True

    elif has_min_max:
        return True

    elif has_value:
        return True

    else:
        return False


def _valid_optimizer_value(constraint):
    if "optimizer_value" not in constraint:
        return True
    elif 0.0 <= constraint["optimizer_value"] <= 1.0:
        return True
    else:
        return False


def _validate_constraints(input_data):
    """
    :param input_data: User constraints and optimizer values
    :type input_data: dict
    :return: Tuple of lists with error messages
    :rtype: tuple
    """
    event_errors = []
    value_errors = []

    event_error_msg = "Well: {}, index: {}, constraint: {}, entry: {}"
    value_error_msg = (
        "Well: {}, in period with index: {}, constraint: {}, "
        "has an optimizer value outside [0, 1], value: {}"
    )

    for well, periods in input_data.items():
        for index, events in periods.items():
            for var_name, constraint in events.items():
                if not _valid_event(constraint):
                    event_errors.append(
                        event_error_msg.format(well, index, var_name, constraint)
                    )
                if not _valid_optimizer_value(constraint):
                    value_errors.append(
                        value_error_msg.format(
                            well, index, var_name, constraint["optimizer_value"]
                        )
                    )

    return event_errors, value_errors


def _filter_keys(input_list, *keys):
    """
    Takes a list of dicts and keys and returns a list of dicts with only input keys
    :param input_list: list of dicts
    :param keys: arbitrary number of keys given as strings
    :return: list of dicts with only input keys
    :rtype: list
    """
    keys = set(keys)
    return [
        {k: v for k, v in i.items() if k in keys} for i in input_list if keys <= set(i)
    ]


def _validate_time(well_dates, well_names_constraints):
    """
    Filters out wells from Everest config which doesn't have a readydate and
    returns names of wells with readydate.
    :param well_dates: list of dicts
    :param well_names_constraints: list of well names from input constraints
    :return: list of well names where the well has constraints, but no date is given
    """

    well_names = _filter_keys(well_dates, "name", "readydate")
    well_names = [well["name"] for well in well_names]

    msg = "Well {} has no start date specified in wells info (keyword: readydate)"

    return [
        msg.format(well) for well in well_names_constraints if well not in well_names
    ]
