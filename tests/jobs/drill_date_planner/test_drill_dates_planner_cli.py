import json
import pathlib
import sys
from typing import Dict, NamedTuple, Tuple

import pytest
from sub_testdata import DRILL_DATE_PLANNER as TEST_DATA

from everest_models.jobs.fm_drill_date_planner import cli
from everest_models.jobs.shared.models import Wells
from everest_models.jobs.shared.validators import parse_file


@pytest.fixture(scope="module")
def drill_date_planner_args():
    return (
        "--input wells.json -opt controls.json --bounds 0.0 1.0"
        " --max-days 300 -o output.json"
    ).split()


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


def test_drill_date_planner_main_entry_point(
    drill_date_planner_args, copy_testdata_tmpdir
) -> None:
    copy_testdata_tmpdir(TEST_DATA)
    cli.main_entry_point(drill_date_planner_args)

    assert (
        pathlib.Path("output.json").read_bytes()
        == pathlib.Path("expected_result.json").read_bytes()
    )


def test_drill_date_planner_lint(drill_date_planner_args, copy_testdata_tmpdir) -> None:
    copy_testdata_tmpdir(TEST_DATA)
    with pytest.raises(SystemExit) as e:
        cli.main_entry_point([*drill_date_planner_args, "--lint"])

    assert e.value.code == 0
    assert not pathlib.Path("output.json").exists()


class Options(NamedTuple):
    input: Wells
    optimizer: Dict[str, float]
    bounds: Tuple[float, float] = (0.1, 1.0)
    max_days: int = 300
    output: pathlib.Path = pathlib.Path("output.json")
    lint: bool = False


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
        cli.main_entry_point(drill_date_planner_args)

    assert e.value.code == 2
    _, err = capsys.readouterr()
    assert "Missing well in controls:\n\tWELL2, WELL4" in err
    assert not pathlib.Path("output.json").exists()


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
        cli.main_entry_point(drill_date_planner_args)

    assert e.value.code == 2
    _, err = capsys.readouterr()
    assert "Drill time missing for well(s):\n\tWELL2, WELL4" in err
    assert not pathlib.Path("output.json").exists()
