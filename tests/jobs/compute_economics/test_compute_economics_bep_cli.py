import copy
import datetime
import logging
import pathlib
from unittest.mock import patch

import pytest
from everest_models.jobs.fm_compute_economics import cli
from everest_models.jobs.fm_compute_economics.economic_indicator_config_model import (
    EconomicIndicatorConfig,
)
from everest_models.jobs.shared.models.wells import WellConfig
from everest_models.jobs.shared.validators import parse_file, valid_input_file
from jobs.compute_economics.parser import (
    MockParser,
    Options,
    ecl_summary_economic_indicator,
)
from sub_testdata import ECONOMIC_INDICATOR as TEST_DATA

_CONFIG_FILE = "input_data.yml"
_CONFIG_FILE_NO_WELL_COSTS = "input_data_no_well_costs.yml"
_WELL_COSTS_N_INPUT_PAIR_ERR_MSG = (
    "-c/--config argument file key 'well_cost' and -i/--input argument file "
    "must always be paired; one of the two is missing."
)


@pytest.fixture(scope="module")
def economic_indicator_input_dict(path_test_data):
    return valid_input_file(path_test_data / TEST_DATA / _CONFIG_FILE)


@pytest.fixture(scope="module")
def economic_indicator_input_no_well_costs_dict(path_test_data):
    return valid_input_file(path_test_data / TEST_DATA / _CONFIG_FILE_NO_WELL_COSTS)


@pytest.fixture(scope="module")
def economic_indicator_summary():
    return ecl_summary_economic_indicator()


@pytest.mark.parametrize(
    "input_file", ("wells.json", "wells_completion_dates.json", "wells_mix_dates.json")
)
@patch("everest_models.jobs.fm_compute_economics.manager.EclipseSummary.get_summary")
@patch("everest_models.jobs.shared.models.wells.WellConfig.parse_file")
def test_bep_main_entry_point(
    mocker_well_config,
    mocker_summary,
    copy_testdata_tmpdir,
    monkeypatch,
    input_file,
    economic_indicator_input_dict,
    economic_indicator_summary,
):
    copy_testdata_tmpdir(TEST_DATA)

    config = copy.deepcopy(economic_indicator_input_dict)
    config["wells_input"] = "./dummy.txt"

    mocker_summary.side_effect = [economic_indicator_summary, None]
    mocker_well_config.return_value = parse_file(input_file, WellConfig)

    monkeypatch.setattr(
        cli,
        "build_argument_parser",
        lambda: MockParser(
            options=Options(
                calculation="bep",
                config=EconomicIndicatorConfig.parse_obj(config),
            )
        ),
    )
    cli.main_entry_point()
    assert pathlib.Path("test_0").read_text() == "25.15"


@patch("everest_models.jobs.fm_compute_economics.manager.EclipseSummary.get_summary")
def test_bep_main_entry_point_no_input_error(
    mocker_summary,
    copy_testdata_tmpdir,
    monkeypatch,
    capsys,
    economic_indicator_input_dict,
    economic_indicator_summary,
):
    copy_testdata_tmpdir(TEST_DATA)

    config = copy.deepcopy(economic_indicator_input_dict)
    mocker_summary.side_effect = [economic_indicator_summary, None]

    monkeypatch.setattr(
        cli,
        "build_argument_parser",
        lambda: MockParser(
            options=Options(
                calculation="bep",
                config=EconomicIndicatorConfig.parse_obj(config),
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
@patch("everest_models.jobs.fm_compute_economics.manager.EclipseSummary.get_summary")
@patch("everest_models.jobs.shared.models.wells.WellConfig.parse_file")
def test_bep_main_entry_point_no_well_costs_error(
    mocker_well_config,
    mocker_summary,
    copy_testdata_tmpdir,
    monkeypatch,
    capsys,
    input_file,
    economic_indicator_input_no_well_costs_dict,
    economic_indicator_summary,
):
    copy_testdata_tmpdir(TEST_DATA)

    config = copy.deepcopy(economic_indicator_input_no_well_costs_dict)
    config["wells_input"] = "./dummy.txt"

    mocker_summary.side_effect = [economic_indicator_summary, None]
    mocker_well_config.return_value = parse_file(input_file, WellConfig)

    monkeypatch.setattr(
        cli,
        "build_argument_parser",
        lambda: MockParser(
            options=Options(
                calculation="bep",
                config=EconomicIndicatorConfig.parse_obj(config),
            )
        ),
    )
    with pytest.raises(SystemExit) as e:
        cli.main_entry_point()
    assert e.value.code == 2
    _, err = capsys.readouterr()
    assert (_WELL_COSTS_N_INPUT_PAIR_ERR_MSG) in err


@patch("everest_models.jobs.fm_compute_economics.manager.EclipseSummary.get_summary")
@patch("everest_models.jobs.shared.models.wells.WellConfig.parse_file")
def test_bep_main_entry_point_no_input(
    mocker_well_config,
    mocker_summary,
    copy_testdata_tmpdir,
    monkeypatch,
    economic_indicator_input_no_well_costs_dict,
    economic_indicator_summary,
):
    copy_testdata_tmpdir(TEST_DATA)

    config = copy.deepcopy(economic_indicator_input_no_well_costs_dict)
    mocker_summary.side_effect = [economic_indicator_summary, None]
    mocker_well_config.return_value = None

    monkeypatch.setattr(
        cli,
        "build_argument_parser",
        lambda: MockParser(
            options=Options(
                calculation="bep",
                config=EconomicIndicatorConfig.parse_obj(config),
            )
        ),
    )
    cli.main_entry_point()
    assert pathlib.Path("test_0").read_text() == "13.63"


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
@patch("everest_models.jobs.fm_compute_economics.manager.EclipseSummary.get_summary")
@patch("everest_models.jobs.shared.models.wells.WellConfig.parse_file")
def test_bep_main_entry_point_overwrite_config(
    mocker_well_config,
    mocker_summary,
    copy_testdata_tmpdir,
    monkeypatch,
    caplog,
    option,
    value,
    economic_indicator_input_no_well_costs_dict,
    economic_indicator_summary,
):
    copy_testdata_tmpdir(TEST_DATA)

    config = copy.deepcopy(economic_indicator_input_no_well_costs_dict)
    mocker_summary.side_effect = [economic_indicator_summary, None]
    mocker_well_config.return_value = None

    monkeypatch.setattr(
        cli,
        "build_argument_parser",
        lambda: MockParser(
            options=Options(
                calculation="bep",
                config=EconomicIndicatorConfig.parse_obj(config),
                **{option: value},
            )
        ),
    )
    with caplog.at_level(logging.INFO):
        cli.main_entry_point()

    assert (
        f"Overwrite config field with '{option}' CLI argument: {value}" in caplog.text
    )


@patch("everest_models.jobs.fm_compute_economics.manager.EclipseSummary.get_summary")
@patch("everest_models.jobs.shared.models.wells.WellConfig.parse_file")
def test_bep_main_entry_lint_ignore_overwrite_config(
    mocker_well_config,
    mocker_summary,
    copy_testdata_tmpdir,
    monkeypatch,
    caplog,
    economic_indicator_input_no_well_costs_dict,
    economic_indicator_summary,
):
    copy_testdata_tmpdir(TEST_DATA)

    config = copy.deepcopy(economic_indicator_input_no_well_costs_dict)
    mocker_summary.side_effect = [economic_indicator_summary, None]
    mocker_well_config.return_value = None

    monkeypatch.setattr(
        cli,
        "build_argument_parser",
        lambda: MockParser(
            options=Options(
                calculation="bep",
                config=EconomicIndicatorConfig.parse_obj(config),
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
