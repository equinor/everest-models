import json
import pathlib
import typing
from functools import partial

import pytest
import ruamel.yaml as yaml
from sub_testdata import WELL_CONSTRAINTS as TEST_DATA

from everest_models.jobs.fm_well_constraints import cli, parser
from everest_models.jobs.fm_well_constraints.models import (
    Constraints,
    WellConstraintConfig,
)


@pytest.fixture(scope="module")
def well_constraints_args() -> typing.List[str]:
    return [
        "--output",
        "well_constraint_output.json",
        "--config",
        "well_constraint_input.yml",
        "--input",
        "wells.json",
        "--rate-constraint",
        "rate_input.json",
        "--phase-constraint",
        "phase_input.json",
    ]


def _get_modified_constraints(path: pathlib.Path, key: str):
    with path.open(mode="r") as fp:
        data = json.load(fp)
    data[key] = data.pop("INJECT2")
    return Constraints.parse_obj(data)


@pytest.fixture(scope="module")
def rate_constraint_parser_action(path_test_data):
    return _get_modified_constraints(
        path_test_data / TEST_DATA / "rate_input.json", "RATE"
    )


@pytest.fixture(scope="module")
def phase_constraint_parser_action(path_test_data):
    return _get_modified_constraints(
        path_test_data / TEST_DATA / "phase_input.json", "PHASE"
    )


@pytest.fixture(scope="module")
def constraints_parser_action_injector(
    phase_constraint_parser_action, rate_constraint_parser_action
):
    return (6, rate_constraint_parser_action), (7, phase_constraint_parser_action)


@pytest.fixture(scope="module")
def well_config_parser_action_injector(path_test_data):
    data = yaml.YAML(typ="safe", pure=True).load(
        (path_test_data / TEST_DATA / "well_constraint_input.yml").read_bytes()
    )
    data["PRODUCE1"] = data.pop("INJECT2")
    return (5, WellConstraintConfig.parse_obj(data))


def build_argument_parser(injections):
    parser_ = parser.build_argument_parser()

    def not_anonymous(_, data):
        return data

    for index, data in injections:
        parser_._actions[index].type = partial(not_anonymous, data=data)
    return parser_


def test_well_constraints_main_entry_point(copy_testdata_tmpdir, well_constraints_args):
    copy_testdata_tmpdir(TEST_DATA)

    cli.main_entry_point(well_constraints_args)

    assert (
        pathlib.Path(well_constraints_args[1]).read_bytes()
        == pathlib.Path("expected_output.json").read_bytes()
    )


def test_well_constraints_main_entry_point_missing_start_date_error(
    copy_testdata_tmpdir,
    monkeypatch,
    well_config_parser_action_injector,
    well_constraints_args,
    capsys,
):
    copy_testdata_tmpdir(TEST_DATA)

    monkeypatch.setattr(
        cli,
        "build_argument_parser",
        partial(
            build_argument_parser,
            injections=(well_config_parser_action_injector,),
        ),
    )

    with pytest.raises(SystemExit) as e:
        cli.main_entry_point(well_constraints_args)
    assert e.value.code == 2
    _, err = capsys.readouterr()
    assert (
        "Missing start date (keyword: readydate) for the following wells:\n\tPRODUCE1"
        in err
    )


def test_well_constraints_main_entry_point_key_mismatch_error(
    copy_testdata_tmpdir,
    monkeypatch,
    constraints_parser_action_injector,
    well_constraints_args,
    capsys,
):
    copy_testdata_tmpdir(TEST_DATA)

    monkeypatch.setattr(
        cli,
        "build_argument_parser",
        partial(
            build_argument_parser,
            injections=constraints_parser_action_injector,
        ),
    )

    with pytest.raises(SystemExit) as e:
        cli.main_entry_point(well_constraints_args)
    assert e.value.code == 2
    _, err = capsys.readouterr()
    assert (
        "Constraint well name keys do not match input well names:"
        "\n\trate_constraints:\n\t\tRATE\n\tphase_constraints:\n\t\tPHASE" in err
    )


def test_well_constraints_main_entry_point_all_file_mismatch_error(
    copy_testdata_tmpdir,
    monkeypatch,
    constraints_parser_action_injector,
    well_config_parser_action_injector,
    well_constraints_args,
    capsys,
):
    copy_testdata_tmpdir(TEST_DATA)

    monkeypatch.setattr(
        cli,
        "build_argument_parser",
        partial(
            build_argument_parser,
            injections=(
                well_config_parser_action_injector,
                *constraints_parser_action_injector,
            ),
        ),
    )

    with pytest.raises(SystemExit) as e:
        cli.main_entry_point(well_constraints_args)
    assert e.value.code == 2
    _, err = capsys.readouterr()
    assert (
        "Missing start date (keyword: readydate) for the following wells:\n\tPRODUCE1"
        in err
    )
    assert (
        "Constraint well name keys do not match input well names:"
        "\n\trate_constraints:\n\t\tRATE\n\tphase_constraints:\n\t\tPHASE"
    ) in err


def test_well_constraints_main_entry_point_lint(
    well_constraints_args, copy_testdata_tmpdir
):
    copy_testdata_tmpdir(TEST_DATA)

    with pytest.raises(SystemExit) as e:
        cli.main_entry_point([*well_constraints_args, "--lint"])

    assert e.value.code == 0
