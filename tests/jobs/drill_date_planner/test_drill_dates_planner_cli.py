import json
import sys
from pathlib import Path
from typing import Any, Dict, NamedTuple, Tuple

import pytest
from sub_testdata import DRILL_DATE_PLANNER as TEST_DATA

from everest_models.jobs.fm_drill_date_planner import cli
from everest_models.jobs.shared.models import Wells
from everest_models.jobs.shared.validators import parse_file


@pytest.fixture(scope="module")
def drill_date_planner_args():
    return ["-opt", "controls.json", "-o", "output.json"]


def missing_controls() -> Dict[str, float]:
    with open("controls.json") as fp:
        controls = json.load(fp)
    del controls["WELL2"]
    del controls["WELL4"]
    return controls


def missing_well() -> Wells:
    with open("wells.json") as fp:
        wells = json.load(fp)
    return Wells.model_validate([well for well in wells if int(well["name"][-1]) % 2])


@pytest.mark.parametrize("wells_input", ["json", "config"])
def test_drill_date_planner_main_entry_point(
    drill_date_planner_args, copy_testdata_tmpdir, wells_input, add_wells_to_config
) -> None:
    copy_testdata_tmpdir(TEST_DATA)
    if wells_input == "json":
        args = (*drill_date_planner_args, "--input", "wells.json")
    else:
        args = (*drill_date_planner_args, "--config", "config.yml")
        add_wells_to_config("wells.json", "config.yml")
    cli.main_entry_point([*args])

    assert Path("output.json").read_bytes() == Path("expected_result.json").read_bytes()


@pytest.mark.parametrize("wells_input", ["json", "config"])
def test_drill_date_planner_lint(
    drill_date_planner_args, copy_testdata_tmpdir, wells_input, add_wells_to_config
) -> None:
    copy_testdata_tmpdir(TEST_DATA)
    if wells_input == "json":
        args = (*drill_date_planner_args, "--input", "wells.json")
    else:
        args = (*drill_date_planner_args, "--config", "config.yml")
        add_wells_to_config("wells.json", "config.yml")
        Path("wells.json").unlink()
    with pytest.raises(SystemExit) as e:
        cli.main_entry_point([*args, "--lint"])

    assert e.value.code == 0
    assert not Path("output.json").exists()


class ConfigMock(NamedTuple):
    wells: dict[str, Any] = {}


class Options(NamedTuple):
    input: Wells
    optimizer: Dict[str, float]
    bounds: Tuple[float, float] = (0.1, 1.0)
    max_days: int = 300
    output: Path = Path("output.json")
    lint: bool = False
    config: ConfigMock = ConfigMock(wells={})


class MockParser:
    def __init__(self, options: Options):
        self._options = options

    def parse_args(self, *args, **kwargs):
        return self._options

    def error(self, message):
        sys.stderr.write(message)
        sys.exit(2)


def test_drill_date_planner_missing_control(
    drill_date_planner_args, monkeypatch, capsys, copy_testdata_tmpdir
) -> None:
    copy_testdata_tmpdir(TEST_DATA)
    with open("controls.json") as fp:
        controls = json.load(fp)

    monkeypatch.setattr(
        cli,
        "build_argument_parser",
        lambda: MockParser(Options(input=missing_well(), optimizer=controls)),
    )

    with pytest.raises(SystemExit) as e:
        cli.main_entry_point(["--input", "wells.json", *drill_date_planner_args])

    assert e.value.code == 2
    _, err = capsys.readouterr()
    assert "Missing well in controls:\n\tWELL2, WELL4" in err
    assert not Path("output.json").exists()


def test_drill_date_planner_missing_well(
    drill_date_planner_args, monkeypatch, capsys, copy_testdata_tmpdir
) -> None:
    copy_testdata_tmpdir(TEST_DATA)
    monkeypatch.setattr(
        cli,
        "build_argument_parser",
        lambda: MockParser(
            Options(
                input=parse_file("wells.json", Wells),
                optimizer=missing_controls(),
            )
        ),
    )

    with pytest.raises(SystemExit) as e:
        cli.main_entry_point(["--input", "wells.json", *drill_date_planner_args])

    assert e.value.code == 2
    _, err = capsys.readouterr()
    assert "Drill time missing for well(s):\n\tWELL2, WELL4" in err
    assert not Path("output.json").exists()


def test_drill_dates_planner_error_no_wells_in_input_or_config(
    copy_testdata_tmpdir, drill_date_planner_args, capsys
):
    copy_testdata_tmpdir(TEST_DATA)
    with pytest.raises(SystemExit) as e:
        cli.main_entry_point([*drill_date_planner_args])

    assert e.value.code == 2
    _, err = capsys.readouterr()
    assert "either --input or config.wells must be provided!" in err


def test_drill_dates_planner_error_both_wells_in_input_and_config(
    copy_testdata_tmpdir, drill_date_planner_args, add_wells_to_config, capsys
):
    copy_testdata_tmpdir(TEST_DATA)
    add_wells_to_config("wells.json", "config.yml")
    with pytest.raises(SystemExit) as e:
        cli.main_entry_point(
            [
                *drill_date_planner_args,
                "--input",
                "wells.json",
                "--config",
                "config.yml",
            ]
        )

    assert e.value.code == 2
    _, err = capsys.readouterr()
    assert "--input and config.wells are mutually exclusive!" in err
