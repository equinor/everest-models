import os

import pytest

from spinningjenny import load_yaml, write_yaml_to_file
from spinningjenny.script import fm_well_constraints
from spinningjenny.well_constraints import well_constraint_job

_CONFIG_FILE = "well_constraint_input.yml"
_TEST_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "../tests/testdata/well_constraints/"
)
_USER_CONFIG = os.path.join(_TEST_DIR, _CONFIG_FILE)
_RATE_CONSTRAINT = os.path.join(_TEST_DIR, "rate_input.json")
_PHASE_CONSTRAINT = os.path.join(_TEST_DIR, "phase_input.json")
_WELL_ORDER = os.path.join(_TEST_DIR, "wells.json")


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
