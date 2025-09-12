from pathlib import Path

import pytest
from sub_testdata import ADD_TEMPLATE as TEST_DATA

from everest_models.jobs.fm_add_templates.cli import main_entry_point


@pytest.fixture(scope="module")
def add_template_args() -> list[str]:
    return ["--config", "config.yml", "--output", "out_test.json"]


def test_main_entry_point(copy_testdata_tmpdir, add_template_args, caplog):
    # caplog-> internal pytest fixture, for usage examples check:
    # https://docs.pytest.org/en/latest/logging.html
    copy_testdata_tmpdir(TEST_DATA)
    main_entry_point([*add_template_args, "--input", "wells.json"])
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

    assert Path("out_test.json").read_bytes() == Path("expected_out.json").read_bytes()


def test_config_file_not_found(capsys):
    # capsys-> internal pytest fixture, for usage examples check:
    # https://docs.pytest.org/en/latest/capture.html

    args = ["--config", "not_found.yml"]

    with pytest.raises(SystemExit) as e:
        main_entry_point(args)

    assert e.value.code == 2
    _, err = capsys.readouterr()

    assert "The path 'not_found.yml' is a directory or file not found.\n" in err


@pytest.mark.parametrize("wells_input", ["json", "config"])
def test_config_file_wrong_opname(
    copy_testdata_tmpdir, add_template_args, add_wells_to_config, wells_input, capsys
):
    # capsys-> internal pytest fixture, for usage examples check:
    # https://docs.pytest.org/en/latest/capture.html
    copy_testdata_tmpdir(TEST_DATA)
    if wells_input == "json":
        args = (*add_template_args, "--input", "wrong_opname.json")
    else:
        args = add_template_args
        add_wells_to_config("wrong_opname.json", "config.yml")
    with pytest.raises(SystemExit) as e:
        main_entry_point([*args])

    assert e.value.code == 2
    _, err = capsys.readouterr()

    assert (
        "No template matched:\nWell: w2\n\toperation: WRONG\tdate: 2000-02-22\n" in err
    )


def test_add_templates_error_no_wells_in_input_or_config(
    copy_testdata_tmpdir, add_template_args, capsys
):
    copy_testdata_tmpdir(TEST_DATA)
    with pytest.raises(SystemExit) as e:
        main_entry_point([*add_template_args])

    assert e.value.code == 2
    _, err = capsys.readouterr()
    assert "either --input or config.wells must be provided!" in err


def test_add_templates_error_both_wells_in_input_and_config(
    copy_testdata_tmpdir, add_template_args, add_wells_to_config, capsys
):
    copy_testdata_tmpdir(TEST_DATA)
    add_wells_to_config("wells.json", "config.yml")
    with pytest.raises(SystemExit) as e:
        main_entry_point([*add_template_args, "--input", "wells.json"])

    assert e.value.code == 2
    _, err = capsys.readouterr()
    assert "--input and config.wells are mutually exclusive!" in err


@pytest.mark.parametrize("wells_input", ["json", "config"])
def test_add_template_lint(
    add_template_args, copy_testdata_tmpdir, wells_input, add_wells_to_config
):
    copy_testdata_tmpdir(TEST_DATA)
    if wells_input == "json":
        args = (*add_template_args, "--input", "wells.json")
    else:
        args = add_template_args
        add_wells_to_config("wells.json", "config.yml")
        Path("wells.json").unlink()
    with pytest.raises(SystemExit) as e:
        main_entry_point([*args, "--lint"])

    assert e.value.code == 0
    assert not Path("out_test.json").exists()


def test_add_template_empty_input_file(add_template_args, copy_testdata_tmpdir, capsys):
    copy_testdata_tmpdir(TEST_DATA)
    path = Path("empty.json")
    path.touch()
    with pytest.raises(SystemExit) as e:
        main_entry_point([*add_template_args, "--input", "empty.json"])

    assert e.value.code == 2
    _, err = capsys.readouterr()
    assert (
        f"\nInvalid file syntax:\n{path.absolute()}\nExpecting value: line 1 column 1 (char 0)\n"
        in err
    )
    assert not Path("out_test.json").exists()
