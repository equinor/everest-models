import json

import pytest
from sub_testdata import ADD_TEMPLATE as TEST_DATA

from spinningjenny.jobs.fm_add_templates.cli import main_entry_point


def test_main_entry_point(copy_testdata_tmpdir, caplog):
    # caplog-> internal pytest fixture, for usage examples check:
    # https://docs.pytest.org/en/latest/logging.html
    copy_testdata_tmpdir(TEST_DATA)

    args = [
        "--config",
        "config.yml",
        "--input",
        "wells.json",
        "--output",
        "out_test.json",
    ]

    main_entry_point(args)
    log_messages = [rec.message for rec in caplog.records]

    # Check job gives warning for duplicate templates in config
    assert (
        "Found duplicate template file path ./templates/template_open.tmpl in config file!"
        in log_messages
    )

    # Check job gives warning for unused template
    assert (
        "Template ./templates/notused.tmpl was not inserted, check insertion keys!"
        in log_messages
    )

    with open("out_test.json", "r") as input_file:
        result = json.load(input_file)

    with open("expected_out.json", "r") as input_file:
        expected_result = json.load(input_file)

    assert expected_result == result


def test_config_file_not_found(copy_testdata_tmpdir, capsys):
    # capsys-> internal pytest fixture, for usage examples check:
    # https://docs.pytest.org/en/latest/capture.html
    copy_testdata_tmpdir(TEST_DATA)

    args = ["--config", "not_found.yml"]

    with pytest.raises(SystemExit) as e:
        main_entry_point(args)

    assert e.value.code == 2
    _, err = capsys.readouterr()

    assert "File not found: not_found.yml" in err


def test_config_file_wrong_opname(copy_testdata_tmpdir, capsys):
    # capsys-> internal pytest fixture, for usage examples check:
    # https://docs.pytest.org/en/latest/capture.html
    copy_testdata_tmpdir(TEST_DATA)

    args = [
        "--config",
        "config.yml",
        "--input",
        "wrong_opname.json",
        "--output",
        "out_test.json",
    ]

    with pytest.raises(SystemExit) as e:
        main_entry_point(args)

    assert e.value.code == 2
    _, err = capsys.readouterr()

    assert (
        "No template matched for well:'w2' operation:'WRONG' at date:'2000-02-22'"
        in err
    )
