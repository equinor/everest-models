import pathlib
import typing

import pytest
from sub_testdata import ADD_TEMPLATE as TEST_DATA

from spinningjenny.jobs.fm_add_templates.cli import main_entry_point


@pytest.fixture(scope="module")
def add_template_args() -> typing.List[str]:
    return [
        "--config",
        "config.yml",
        "--output",
        "out_test.json",
        "--input",
    ]


def test_main_entry_point(copy_testdata_tmpdir, add_template_args, caplog):
    # caplog-> internal pytest fixture, for usage examples check:
    # https://docs.pytest.org/en/latest/logging.html
    copy_testdata_tmpdir(TEST_DATA)
    main_entry_point([*add_template_args, "wells.json"])
    log_messages = [rec.message for rec in caplog.records]

    # Check job gives warning for duplicate templates in config
    assert (
        "Found duplicate template file path ./templates/template_open.tmpl in config file!"
        in log_messages
    )

    # Check job gives warning for unused template
    assert (
        "Template(s) not inserted:\n\t./templates/notused.tmpl\n\tPlease, check insertion keys!"
        # "Template ./templates/notused.tmpl was not inserted, check insertion keys!"
        in log_messages
    )

    assert (
        pathlib.Path("out_test.json").read_bytes()
        == pathlib.Path("expected_out.json").read_bytes()
    )


def test_config_file_not_found(capsys):
    # capsys-> internal pytest fixture, for usage examples check:
    # https://docs.pytest.org/en/latest/capture.html

    args = ["--config", "not_found.yml"]

    with pytest.raises(SystemExit) as e:
        main_entry_point(args)

    assert e.value.code == 2
    _, err = capsys.readouterr()

    assert "The path 'not_found.yml' is a directory or file not found.\n" in err


def test_config_file_wrong_opname(copy_testdata_tmpdir, add_template_args, capsys):
    # capsys-> internal pytest fixture, for usage examples check:
    # https://docs.pytest.org/en/latest/capture.html
    copy_testdata_tmpdir(TEST_DATA)
    with pytest.raises(SystemExit) as e:
        main_entry_point([*add_template_args, "wrong_opname.json"])

    assert e.value.code == 2
    _, err = capsys.readouterr()

    assert (
        "No template matched:\nWell: w2\n\toperation: WRONG\tdate: 2000-02-22\n" in err
    )


def test_add_template_lint(add_template_args, copy_testdata_tmpdir):
    copy_testdata_tmpdir(TEST_DATA)
    with pytest.raises(SystemExit) as e:
        main_entry_point([*add_template_args, "wells.json", "--lint"])

    assert e.value.code == 0
    assert not pathlib.Path("out_test.json").exists()


def test_add_template_empty_input_file(add_template_args, copy_testdata_tmpdir, capsys):
    copy_testdata_tmpdir(TEST_DATA)
    pathlib.Path("empty.json").touch()
    with pytest.raises(SystemExit) as e:
        main_entry_point([*add_template_args, "empty.json"])

    assert e.value.code == 2
    _, err = capsys.readouterr()
    assert (
        "The file: 'empty.json' is not a valid json file.\n\t<Expecting value: line 1 column 1 (char 0)>\n"
        in err
    )
    assert not pathlib.Path("out_test.json").exists()
