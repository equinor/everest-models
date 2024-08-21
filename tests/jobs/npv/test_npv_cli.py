import datetime
import logging
import pathlib

import pytest
from jobs.npv.parser import MockParser, Options
from sub_testdata import NPV as TEST_DATA

from everest_models.jobs.fm_npv import cli
from everest_models.jobs.fm_npv.npv_config import NPVConfig
from everest_models.jobs.shared.models import Wells
from everest_models.jobs.shared.validators import parse_file

_CONFIG_FILE = "input_data.yml"
_CONFIG_FILE_NO_WELL_COSTS = "input_data_no_well_costs.yml"
_WELL_COSTS_N_INPUT_PAIR_ERR_MSG = (
    "-c/--config argument file key 'well_cost' and -i/--input argument file "
    "must always be paired; one of the two is missing."
)


@pytest.mark.parametrize(
    "input_file", ("wells.json", "wells_completion_dates.json", "wells_mix_dates.json")
)
def test_npv_main_entry_point(copy_testdata_tmpdir, monkeypatch, input_file):
    copy_testdata_tmpdir(TEST_DATA)
    monkeypatch.setattr(
        cli,
        "build_argument_parser",
        lambda: MockParser(
            options=Options(
                input=parse_file(input_file, Wells),
                config=parse_file(_CONFIG_FILE, NPVConfig),
            )
        ),
    )
    cli.main_entry_point()
    assert pathlib.Path("test_0").read_text() == "691981114.68"


def test_npv_main_entry_point_no_input_error(copy_testdata_tmpdir, monkeypatch, capsys):
    copy_testdata_tmpdir(TEST_DATA)
    monkeypatch.setattr(
        cli,
        "build_argument_parser",
        lambda: MockParser(
            options=Options(
                config=parse_file(_CONFIG_FILE, NPVConfig),
            )
        ),
    )
    with pytest.raises(SystemExit) as e:
        cli.main_entry_point()
    assert e.value.code == 2
    _, err = capsys.readouterr()
    assert (_WELL_COSTS_N_INPUT_PAIR_ERR_MSG) in err


@pytest.mark.parametrize(
    "input_file", ("wells.json", "wells_completion_dates.json", "wells_mix_dates.json")
)
def test_npv_main_entry_point_no_well_costs_error(
    copy_testdata_tmpdir, monkeypatch, capsys, input_file
):
    copy_testdata_tmpdir(TEST_DATA)
    monkeypatch.setattr(
        cli,
        "build_argument_parser",
        lambda: MockParser(
            options=Options(
                input=parse_file(input_file, Wells),
                config=parse_file(_CONFIG_FILE_NO_WELL_COSTS, NPVConfig),
            )
        ),
    )
    with pytest.raises(SystemExit) as e:
        cli.main_entry_point()
    assert e.value.code == 2
    _, err = capsys.readouterr()
    assert (_WELL_COSTS_N_INPUT_PAIR_ERR_MSG) in err


def test_npv_main_entry_point_no_input(copy_testdata_tmpdir, monkeypatch):
    copy_testdata_tmpdir(TEST_DATA)
    monkeypatch.setattr(
        cli,
        "build_argument_parser",
        lambda: MockParser(
            options=Options(
                config=parse_file(_CONFIG_FILE_NO_WELL_COSTS, NPVConfig),
            )
        ),
    )
    cli.main_entry_point()
    assert pathlib.Path("test_0").read_text() == "865092178.90"


@pytest.mark.parametrize(
    "option, value",
    (
        pytest.param("multiplier", 3, id="multiplier"),
        pytest.param("default_exchange_rate", 3.41, id="default_exchange_rate"),
        pytest.param("default_discount_rate", 4.75, id="default_discount_rate"),
        pytest.param("start_date", datetime.date(2000, 12, 7), id="start_date"),
        pytest.param("end_date", datetime.date(2002, 12, 23), id="end_date"),
        pytest.param("ref_date", datetime.date(2000, 12, 9), id="ref_date"),
    ),
)
def test_npv_main_entry_point_overwrite_config(
    copy_testdata_tmpdir, monkeypatch, caplog, option, value
):
    copy_testdata_tmpdir(TEST_DATA)
    monkeypatch.setattr(
        cli,
        "build_argument_parser",
        lambda: MockParser(
            options=Options(
                config=parse_file(_CONFIG_FILE_NO_WELL_COSTS, NPVConfig),
                **{option: value},
            )
        ),
    )
    with caplog.at_level(logging.INFO):
        cli.main_entry_point()

    assert (
        f"Overwrite config field with '{option}' CLI argument: {value}" in caplog.text
    )


def test_npv_main_entry_lint_ignore_overwrite_config(
    copy_testdata_tmpdir, monkeypatch, caplog
):
    copy_testdata_tmpdir(TEST_DATA)
    monkeypatch.setattr(
        cli,
        "build_argument_parser",
        lambda: MockParser(
            options=Options(
                config=parse_file(_CONFIG_FILE_NO_WELL_COSTS, NPVConfig),
                multiplier=1.42,
                lint=True,
            )
        ),
    )
    with pytest.raises(SystemExit) as e:
        cli.main_entry_point()
    assert e.value.code == 0
    assert "Overwrite config field with 'multiplier' CLI argument" not in caplog.text
    assert not pathlib.Path("test_0").exists()
