import pathlib
from typing import Dict, NamedTuple

import pytest
from sub_testdata import INTERPRET_WELL_DRILL as TEST_DATA

from spinningjenny.jobs.fm_interpret_well_drill import cli


@pytest.fixture(scope="module")
def interpret_well_drill_args():
    return (
        "--input",
        "optimizer_values.yml",
        "--output",
        "test.json",
    )


def test_interpret_well_drill_entry(copy_testdata_tmpdir, interpret_well_drill_args):
    copy_testdata_tmpdir(TEST_DATA)
    out_file = "test.json"

    cli.main_entry_point(interpret_well_drill_args)
    assert (
        pathlib.Path(out_file).read_bytes()
        == pathlib.Path("correct_out.json").read_bytes()
    )


def test_interpret_well_drill_lint(copy_testdata_tmpdir, interpret_well_drill_args):
    copy_testdata_tmpdir(TEST_DATA)
    with pytest.raises(SystemExit) as e:
        cli.main_entry_point([*interpret_well_drill_args, "--lint"])

    assert e.value.code == 0
    assert not pathlib.Path("test.json").exists()


class Options(NamedTuple):
    input: Dict[str, str]
    output: pathlib.Path = pathlib.Path("output.json")


def test_interpret_well_drill_bad_input_value(
    copy_testdata_tmpdir, monkeypatch, interpret_well_drill_args, capsys
):
    copy_testdata_tmpdir(TEST_DATA)
    monkeypatch.setattr(
        cli.args_parser,
        "parse_args",
        lambda *args, **kwargs: Options({"w1": ".8", "w2": "."}),
    )

    with pytest.raises(SystemExit) as e:
        cli.main_entry_point(interpret_well_drill_args)

    assert e.value.code == 2
    _, err = capsys.readouterr()

    assert (
        "-i/--input file, Make sure all values in 'key: value' pairs are valid numbers."
        in err
    )
