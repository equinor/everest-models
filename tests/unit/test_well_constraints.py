import os
import shutil
import pytest
import configsuite
import itertools


from copy import deepcopy

from spinningjenny import write_yaml_to_file, load_yaml
from spinningjenny.script import fm_well_constraints
from spinningjenny.well_constraints import well_constraint_job
from spinningjenny.well_constraints import well_config
from spinningjenny.well_constraints import well_constraint_validate

_CONFIG_FILE = "well_constraint_input.yml"
_TEST_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "../tests/testdata/well_constraints/"
)
_USER_CONFIG = os.path.join(_TEST_DIR, _CONFIG_FILE)
_RATE_CONSTRAINT = os.path.join(_TEST_DIR, "rate_input.json")
_PHASE_CONSTRAINT = os.path.join(_TEST_DIR, "phase_input.json")
_WELL_ORDER = os.path.join(_TEST_DIR, "wells.json")


@pytest.fixture
def input_data(tmpdir):
    for file_name in os.listdir(_TEST_DIR):
        shutil.copy(_TEST_DIR + file_name, tmpdir.strpath)

    cwd = os.getcwd()
    tmpdir.chdir()

    yield load_yaml("well_constraint_input.yml")

    os.chdir(cwd)


def test_main_entry_point(tmpdir):
    arguments = [
        "--output",
        "well_constraint_output.json",
        "--input",
        _WELL_ORDER,
        "--config",
        _USER_CONFIG,
        "--rate-constraint",
        _RATE_CONSTRAINT,
        "--phase-constraint",
        _PHASE_CONSTRAINT,
    ]

    cwd = os.getcwd()

    tmpdir.chdir()

    fm_well_constraints.main_entry_point(arguments)
    result_output = load_yaml(
        os.path.join(tmpdir.strpath, "well_constraint_output.json")
    )
    expected_output = load_yaml(os.path.join(_TEST_DIR, "well_constraint_output.json"))

    assert result_output == expected_output

    input_config = load_yaml(_USER_CONFIG)
    invalid_input = {"INJECT1": {1: {"rate": {"value": 100}}}}
    invalid_config = well_constraint_job.merge_dicts(input_config, invalid_input)
    fpath = os.path.join(tmpdir.strpath, "invalid_user_config.yml")
    write_yaml_to_file(invalid_config, fpath)

    arguments[6] = fpath

    with pytest.raises(SystemExit) as wrapped_error:
        fm_well_constraints.main_entry_point(arguments)
    assert wrapped_error.type == SystemExit
    assert wrapped_error.value.code == 2

    invalid_input = {"INJECT1": {2: {"rate": {"value": 100}}}}
    invalid_config = well_constraint_job.merge_dicts(invalid_config, invalid_input)
    fpath = os.path.join(tmpdir.strpath, "invalid_user_config.yml")
    write_yaml_to_file(invalid_config, fpath)

    with pytest.raises(SystemExit) as wrapped_error:
        fm_well_constraints.main_entry_point(arguments)
    assert wrapped_error.type == SystemExit
    assert wrapped_error.value.code == 2

    os.chdir(cwd)


def test_transformation():
    input_dict = {
        "well": {
            1: {
                "var_1": {"optimizer_value": 0.2, "min": 0.0, "max": 1.0},
                "var_2": {"optimizer_value": 0.2, "options": [1, 2]},
                "var_3": {"value": 0.2},
            }
        }
    }
    input_copy = deepcopy(input_dict)

    expected_dict = {
        "well": {
            1: {
                "var_1": {"optimizer_value": 0.2, "min": 0.0, "max": 1.0, "value": 0.2},
                "var_2": {"optimizer_value": 0.2, "options": [1, 2], "value": 1},
                "var_3": {"value": 0.2},
            }
        }
    }

    result_dict = well_constraint_job._insert_transformed_values(input_dict)

    assert input_dict == input_copy
    assert result_dict == expected_dict


def test_transformation_calc():
    test_values = [0, 1, 0.1, 0.2, 0.15684]
    expected_transformation = [0.0, 1000.0, 100.0, 200.0, 156.84]
    expected_index = [0, 0, 0, 1, 1]

    result_transformation = [
        well_constraint_job._calc_number_value(0, 1000, val) for val in test_values
    ]
    assert result_transformation == expected_transformation

    input_phases = ["water", "gas"]
    optimized_values = [0, 0.25, 0.5, 0.75, 1.0]
    expected_phase = ["water", "water", "water", "gas", "gas"]

    result_phase = [
        well_constraint_job._calc_list_value(input_phases, val)
        for val in optimized_values
    ]
    assert result_phase == expected_phase

    result_index = [
        well_constraint_job._find_index(val, input_phases) for val in optimized_values
    ]
    assert result_index == expected_index


def test_transformation_calc_invalid_input():
    input_phases = ["water", "gas"]

    with pytest.raises(ValueError):
        well_constraint_job._calc_list_value(input_phases, 1.1)

    with pytest.raises(ValueError):
        well_constraint_job._calc_list_value(input_phases, -0.1)


def test_dict_merge():
    input_dict_1 = {"well1": {1: {"rate": 123}}, "well2": {1: {"rate": 321}}}
    input_dict_2 = {"well1": {1: {"duration": 456}}}
    expected_dict = {
        "well1": {1: {"rate": 123, "duration": 456}},
        "well2": {1: {"rate": 321}},
    }

    input_dict_1_copy = deepcopy(input_dict_1)
    input_dict_2_copy = deepcopy(input_dict_2)
    result_dict = well_constraint_job.merge_dicts(input_dict_1, input_dict_2)

    assert result_dict == expected_dict
    assert input_dict_1 == input_dict_1_copy
    assert input_dict_2 == input_dict_2_copy

    input_dict_2 = {"something": {5: {"duration": {"new_key": 0.5456}}}}
    expected_dict = {
        "well1": {1: {"rate": 123}},
        "well2": {1: {"rate": 321}},
        "something": {5: {"duration": {"new_key": 0.5456}}},
    }

    result_dict = well_constraint_job.merge_dicts(input_dict_1, input_dict_2)

    assert result_dict == expected_dict


def test_dict_merge_key_overwrite():
    input_dict_1 = {"well1": {1: {"rate": 123}}, "well2": {1: {"rate": 321}}}
    input_dict_2 = {"well1": {1: {"rate": 456}}}
    expected_dict = {"well1": {1: {"rate": 456}}, "well2": {1: {"rate": 321}}}

    input_dict_1_copy = deepcopy(input_dict_1)
    input_dict_2_copy = deepcopy(input_dict_2)
    result_dict = well_constraint_job.merge_dicts(input_dict_1, input_dict_2)

    assert result_dict == expected_dict
    assert input_dict_1 == input_dict_1_copy
    assert input_dict_2 == input_dict_2_copy


def test_dict_merge_three_dicts():
    input_dict_1 = {"well1": {1: {"prop_1": 123}}}
    input_dict_2 = {"well1": {1: {"prop_2": 123}}}
    input_dict_3 = {"well1": {1: {"prop_3": 123}}}

    expected_dict = {"well1": {1: {"prop_1": 123, "prop_2": 123, "prop_3": 123}}}

    input_dict_1_copy = deepcopy(input_dict_1)
    input_dict_2_copy = deepcopy(input_dict_2)
    input_dict_3_copy = deepcopy(input_dict_3)
    result_dict = well_constraint_job.merge_dicts(
        input_dict_1, input_dict_2, input_dict_3
    )

    assert result_dict == expected_dict
    assert input_dict_1 == input_dict_1_copy
    assert input_dict_2 == input_dict_2_copy
    assert input_dict_3 == input_dict_3_copy


def test_dict_merge_invalid_input():

    for arg1, arg2 in itertools.combinations([1, 1.0, "str", (), {}, []], 2):
        with pytest.raises(TypeError):
            well_constraint_job.merge_dicts(arg1, arg2)


def test_config_setup(input_data):
    schema = well_config._build_schema()
    assert well_constraint_validate.valid_configuration(input_data, schema)

    config = configsuite.ConfigSuite(input_data, schema)
    config = config.push({"INJECT1": {1: {"rate": {"min": 2, "max": 1}}}})
    assert not config.valid

    test_data = {"WELL": {1: {"rate": {"value": 50}}}}

    config = configsuite.ConfigSuite(test_data, schema)

    assert not config.valid

    test_data = {
        "WELL": {
            1: {
                "rate": {"value": 50},
                "phase": {"value": "water"},
                "duration": {"value": 50},
            }
        }
    }

    config = configsuite.ConfigSuite(test_data, schema)
    assert config.valid

    test_data_copy = deepcopy(test_data)

    for key in ["phase", "duration", "rate"]:
        test_data = deepcopy(test_data_copy)
        test_data["WELL"][1].pop(key)
        config = configsuite.ConfigSuite(test_data, schema)
        assert not config.valid


def test_config_setup_value():
    element = {"min": 0.0, "max": 1.0}
    assert well_config._value_validation(element)
    element.pop("min")
    assert not well_config._value_validation(element)
    element = {"value": 0.0, "max": 1.0}
    assert not well_config._value_validation(element)
    element.pop("max")
    assert well_config._value_validation(element)
    element = {"value": 0, "min": 0.0, "max": 1.0}
    assert not well_config._value_validation(element)


def test_config_setup_min_max():
    element = {"min": 0.0, "max": 1.0}
    assert well_config._min_max_validation(element)
    element = {"min": 1.0, "max": 0.0}
    assert not well_config._min_max_validation(element)


def test_config_setup_list():
    element = {"value": 1.0}
    assert well_config._list_validation(element)
    element = {"value": 1.0, "options": [1, 2, 3]}
    assert not well_config._list_validation(element)
    element = {"options": [1, 2, 3]}
    assert well_config._list_validation(element)
    element = {}
    assert not well_config._list_validation(element)


def test_add_dates():
    start_date = "2019-01-01"
    test_data = {
        "WELL": {
            1: {
                "rate": {"value": 50},
                "phase": {"value": "water"},
                "duration": {"value": 10},
            },
            2: {
                "rate": {"value": 10},
                "phase": {"value": "surf"},
                "duration": {"value": 50},
            },
        }
    }
    well_dates = [{"name": "WELL", "readydate": start_date}]
    expected_result = [
        {
            "name": "WELL",
            "readydate": start_date,
            "ops": [
                {"opname": "rate", "rate": 50, "phase": "water", "date": start_date},
                {"opname": "rate", "rate": 10, "phase": "surf", "date": "2019-01-11"},
            ],
        }
    ]
    result_data = well_constraint_job._add_dates(test_data, well_dates)

    assert result_data == expected_result

    well_dates = [
        {
            "name": "WELL",
            "readydate": start_date,
            "ops": [{"opname": "open", "date": start_date}],
        }
    ]

    expected_result = [
        {
            "name": "WELL",
            "readydate": start_date,
            "ops": [
                {"opname": "open", "date": start_date},
                {"opname": "rate", "rate": 50, "phase": "water", "date": start_date},
                {"opname": "rate", "rate": 10, "phase": "surf", "date": "2019-01-11"},
            ],
        }
    ]

    result_data = well_constraint_job._add_dates(test_data, well_dates)

    assert result_data == expected_result


def test_validation():
    test_data = {
        "WELL": {
            1: {
                "rate": {"min": 100, "max": 200, "optimizer_value": 1.1},
                "phase": {"options": ["water", "gas"], "optimizer_value": -0.1},
                "duration": {"value": 10},
            },
            2: {
                "rate": {"optimizer_value": 50},
                "duration": {"optimizer_value": 0.1, "value": 10},
            },
        }
    }

    expected_constraint_errors = [
        "Well: WELL, index: 2, constraint: rate, entry: {'optimizer_value': 50}",
        "Well: WELL, index: 2, constraint: duration, entry: {'optimizer_value': 0.1, 'value': 10}",
    ]

    expected_value_errors = [
        "Well: WELL, in period with index: 1, constraint: rate, has an optimizer value outside [0, 1], value: 1.1",
        "Well: WELL, in period with index: 1, constraint: phase, has an optimizer value outside [0, 1], value: -0.1",
        "Well: WELL, in period with index: 2, constraint: rate, has an optimizer value outside [0, 1], value: 50",
    ]

    constraint_errors, value_errors = well_constraint_validate._validate_constraints(
        test_data
    )

    assert len(constraint_errors) == len(expected_constraint_errors)
    assert all([err in expected_constraint_errors for err in constraint_errors])

    assert len(value_errors) == len(expected_value_errors)
    assert all([err in expected_value_errors for err in value_errors])

    test_dates = [{"name": "WELL"}]

    expected_error = [
        "Well WELL has no start date specified in wells info (keyword: readydate)"
    ]

    result_error = well_constraint_validate._validate_time(test_dates, test_data.keys())

    assert result_error == expected_error

    test_dates = [{"name": "WELL", "readydate": "2019-05-12"}]

    assert well_constraint_validate._validate_time(test_dates, test_data.keys()) == []

    assert not well_constraint_validate.valid_job(test_dates, test_data)


def test_inject_key_in_dict():
    test_data = {"name": {"1": 1}}
    key = "value"

    expected_result = {"name": {1: {key: {"optimizer_value": 1}}}}

    result_data = fm_well_constraints._inject_key_in_dict(test_data, key)

    assert result_data == expected_result

    test_data = {"name_1": {"1": 1, "2": 2}, "name_2": {"1": 2}}
    key = "value"

    expected_result = {
        "name_1": {1: {key: {"optimizer_value": 1}}, 2: {key: {"optimizer_value": 2}}},
        "name_2": {1: {key: {"optimizer_value": 2}}},
    }

    result_data = fm_well_constraints._inject_key_in_dict(test_data, key)

    assert result_data == expected_result
