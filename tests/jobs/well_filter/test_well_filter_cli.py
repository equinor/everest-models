import logging
import pathlib

import pytest
from sub_testdata import WELL_FILTER as TEST_DATA

from spinningjenny.jobs.fm_well_filter.cli import main_entry_point


@pytest.fixture(scope="module")
def well_filter_args():
    return (
        "--output",
        "test_wells.json",
        "--input",
        "wells.json",
    )


def test_well_filter_keep_entry(copy_testdata_tmpdir, well_filter_args):
    copy_testdata_tmpdir(TEST_DATA)

    main_entry_point(
        [
            *well_filter_args,
            "--keep",
            "well_names.json",
        ]
    )

    assert (
        pathlib.Path("test_wells.json").read_bytes()
        == pathlib.Path("keep_out.json").read_bytes()
    )


def test_drill_plan_filter_yaml_entry(copy_testdata_tmpdir, well_filter_args):
    copy_testdata_tmpdir(TEST_DATA)

    main_entry_point(
        [
            *well_filter_args,
            "--keep",
            "well_names.yaml",
        ]
    )

    assert (
        pathlib.Path("test_wells.json").read_bytes()
        == pathlib.Path("keep_out.json").read_bytes()
    )


def test_well_filter_remove_entry(copy_testdata_tmpdir, well_filter_args):
    copy_testdata_tmpdir(TEST_DATA)

    main_entry_point(
        [
            *well_filter_args,
            "--remove",
            "well_names.json",
        ]
    )

    assert (
        pathlib.Path("test_wells.json").read_bytes()
        == pathlib.Path("remove_out.json").read_bytes()
    )


def test_well_filter_both_remove_n_keep(copy_testdata_tmpdir, well_filter_args, capsys):
    copy_testdata_tmpdir(TEST_DATA)

    with pytest.raises(SystemExit) as e:
        main_entry_point(
            [
                *well_filter_args,
                "--remove",
                "well_names.json",
                "--keep",
                "well_names.json",
            ]
        )
    assert e.value.code == 2

    _, err = capsys.readouterr()

    assert "argument -k/--keep: not allowed with argument -r/--remove" in err


def test_well_filter_neither_remove_n_keep(
    copy_testdata_tmpdir, well_filter_args, capsys
):
    copy_testdata_tmpdir(TEST_DATA)

    with pytest.raises(SystemExit) as e:
        main_entry_point(
            well_filter_args,
        )
    assert e.value.code == 2

    _, err = capsys.readouterr()

    assert "one of the arguments -k/--keep -r/--remove is required" in err


def test_add_template_lint(copy_testdata_tmpdir, well_filter_args):
    copy_testdata_tmpdir(TEST_DATA)
    with pytest.raises(SystemExit) as e:
        main_entry_point([*well_filter_args, "--keep", "well_names.json", "--lint"])

    assert e.value.code == 0
    assert not pathlib.Path("test_wells.json").exists()


def test_well_filter_keep_bad_entry(copy_testdata_tmpdir, well_filter_args, caplog):
    copy_testdata_tmpdir(TEST_DATA)

    with caplog.at_level(logging.WARNING):
        main_entry_point([*well_filter_args, "--keep", "bad_well_names.json"])

    assert len(caplog.records) == 1
    assert "Keep value(s) are not present in input file:\n\t" in caplog.text
    assert all(value in caplog.text for value in ("INJ2", "PRD2"))


def test_well_filter_remove_bad_entry(copy_testdata_tmpdir, well_filter_args, caplog):
    copy_testdata_tmpdir(TEST_DATA)

    with caplog.at_level(logging.WARNING):
        main_entry_point(
            [
                *well_filter_args,
                "--remove",
                "bad_well_names.json",
            ]
        )

    assert len(caplog.records) == 1
    assert "Remove value(s) are not present in input file:\n\t" in caplog.text
    assert all(value in caplog.text for value in ("INJ2", "PRD2"))
