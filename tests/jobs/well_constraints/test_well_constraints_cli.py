import os

import pytest

from jobs.fm_well_constraints import cli, well_constraint_job
from jobs.utils.io_utils import load_yaml, write_yaml_to_file


def test_main_entry_point(tmpdir, path_test_data):
    constraint_testdata = path_test_data / "well_constraints"
    user_config = str(constraint_testdata / "well_constraint_input.yml")
    arguments = [
        "--output",
        "well_constraint_output.json",
        "--input",
        str(constraint_testdata / "wells.json"),
        "--config",
        user_config,
        "--rate-constraint",
        str(constraint_testdata / "rate_input.json"),
        "--phase-constraint",
        str(constraint_testdata / "phase_input.json"),
    ]

    cwd = os.getcwd()

    tmpdir.chdir()

    cli.main_entry_point(arguments)
    result_output = load_yaml(
        os.path.join(tmpdir.strpath, "well_constraint_output.json")
    )
    expected_output = load_yaml(constraint_testdata / "well_constraint_output.json")

    assert result_output == expected_output

    input_config = load_yaml(user_config)
    invalid_input = {"INJECT1": {1: {"rate": {"value": 100}}}}
    invalid_config = well_constraint_job.merge_dicts(input_config, invalid_input)
    fpath = os.path.join(tmpdir.strpath, "invalid_user_config.yml")
    write_yaml_to_file(invalid_config, fpath)

    arguments[6] = fpath

    with pytest.raises(SystemExit) as wrapped_error:
        cli.main_entry_point(arguments)
    assert wrapped_error.type == SystemExit
    assert wrapped_error.value.code == 2

    invalid_input = {"INJECT1": {2: {"rate": {"value": 100}}}}
    invalid_config = well_constraint_job.merge_dicts(invalid_config, invalid_input)
    fpath = os.path.join(tmpdir.strpath, "invalid_user_config.yml")
    write_yaml_to_file(invalid_config, fpath)

    with pytest.raises(SystemExit) as wrapped_error:
        cli.main_entry_point(arguments)
    assert wrapped_error.type == SystemExit
    assert wrapped_error.value.code == 2

    os.chdir(cwd)
