import pathlib
from typing import Tuple

import pytest
from sub_testdata import SCHMERGE as TEST_DATA

from everest_models.jobs.fm_schmerge.cli import main_entry_point


@pytest.fixture(scope="module")
def schmerge_args() -> Tuple[str, ...]:
    return (
        "--output",
        "out.sch",
        "--schedule",
        "loaded_dates.sch",
        "--input",
        "wells.json",
    )


def test_schmerge_main_entry_point(copy_testdata_tmpdir, schmerge_args):
    copy_testdata_tmpdir(TEST_DATA)

    main_entry_point(schmerge_args)

    assert (
        pathlib.Path("result.sch").read_bytes() == pathlib.Path("out.sch").read_bytes()
    )


def test_schmerge_main_entry_point_invalid_wells(
    copy_testdata_tmpdir, schmerge_args, capsys
):
    copy_testdata_tmpdir(TEST_DATA)

    with pytest.raises(SystemExit) as e:
        main_entry_point([*schmerge_args[:-1], "invalid_wells.json"])

    assert e.value.code == 2
    _, err = capsys.readouterr()

    assert (
        "argument -i/--input: \nindex 1 -> ops -> index 1 -> template:\n\tField required"
        in err
    )


def test_schmerge_entry_lint(copy_testdata_tmpdir, schmerge_args):
    copy_testdata_tmpdir(TEST_DATA)

    with pytest.raises(SystemExit) as e:
        main_entry_point([*schmerge_args, "--lint"])

    assert e.value.code == 0
    assert not pathlib.Path("out.sch").exists()
