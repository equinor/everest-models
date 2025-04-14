import datetime
import logging
import pathlib

import pytest
from jobs.compute_economics.parser import Options
from sub_testdata import ECONOMIC_INDICATOR as TEST_DATA

from everest_models.jobs.fm_compute_economics import cli
from everest_models.jobs.fm_compute_economics.economic_indicator_config_model import (
    EconomicIndicatorConfig,
)


@pytest.mark.parametrize(
    "calculation_type, wells_file, expected",
    (
        pytest.param("npv", "wells.json", "691981114.68", id="npv wells.json"),
        pytest.param(
            "npv",
            "wells_completion_dates.json",
            "691981114.68",
            id="npv wells_completion_dates.json",
        ),
        pytest.param(
            "npv", "wells_mix_dates.json", "691981114.68", id="npv wells_mix_dates.json"
        ),
        pytest.param("bep", "wells.json", "25.15", id="bep wells.json"),
        pytest.param(
            "bep",
            "wells_completion_dates.json",
            "25.15",
            id="bep wells_completion_dates.json",
        ),
        pytest.param(
            "bep", "wells_mix_dates.json", "25.15", id="bep wells_mix_dates.json"
        ),
    ),
)
def test_economic_indicator_main_entry_point(
    calculation_type,
    wells_file,
    expected,
    copy_testdata_tmpdir,
    modify_economic_config,
    build_economic_parser_patch,
    get_summary_patch,
):
    copy_testdata_tmpdir(TEST_DATA)
    build_economic_parser_patch(
        modify_economic_config(wells_file), calculation=calculation_type
    )

    cli.main_entry_point()
    assert pathlib.Path("test").read_text() == expected


@pytest.mark.parametrize(
    "wells_file", ("wells.json", "wells_completion_dates.json", "wells_mix_dates.json")
)
def test_economic_indicator_main_entry_point_npv_output_currency_USD(
    wells_file,
    copy_testdata_tmpdir,
    modify_economic_config,
    build_economic_parser_patch,
    get_summary_patch,
):
    copy_testdata_tmpdir(TEST_DATA)
    build_economic_parser_patch(
        modify_economic_config(wells_file, currency="USD"), calculation="npv"
    )

    cli.main_entry_point()
    assert pathlib.Path("test").read_text() == "77942465.48"


@pytest.mark.parametrize(
    "calculation_type, input_file, remove_well_costs",
    (
        pytest.param("bep", "wells.json", True, id="bep No well costs"),
        pytest.param("bep", None, False, id="bep No input wells"),
        pytest.param("npv", "wells.json", True, id="npv No well costs"),
        pytest.param("npv", None, False, id="npv No input wells"),
    ),
)
def test_economic_indicator_main_entry_point_pairing_error(
    calculation_type,
    copy_testdata_tmpdir,
    capsys,
    input_file,
    remove_well_costs,
    modify_economic_config,
    build_economic_parser_patch,
    get_summary_patch,
):
    copy_testdata_tmpdir(TEST_DATA)

    build_economic_parser_patch(
        modify_economic_config(input_file, remove_well_costs=remove_well_costs),
        calculation=calculation_type,
    )

    with pytest.raises(SystemExit) as e:
        cli.main_entry_point()
    assert e.value.code == 2
    _, err = capsys.readouterr()
    assert (
        "-c/--config argument file keys 'well_costs' and 'wells_input' "
        "must always be paired; one of the two is missing."
    ) in err


@pytest.mark.parametrize(
    "calculation_type, expected",
    (
        pytest.param("bep", "13.63", id="bep"),
        pytest.param("npv", "865092178.90", id="npv"),
    ),
)
def test_economic_indicator_main_entry_point_no_input(
    calculation_type,
    expected,
    copy_testdata_tmpdir,
    modify_economic_config,
    build_economic_parser_patch,
    get_summary_patch,
):
    copy_testdata_tmpdir(TEST_DATA)
    build_economic_parser_patch(
        modify_economic_config(remove_well_costs=True), calculation=calculation_type
    )

    cli.main_entry_point()
    assert pathlib.Path("test").read_text() == expected


@pytest.mark.parametrize(
    "option, value",
    (
        pytest.param("summary_reference", "junk.UNSMRY", id="summary_reference"),
        pytest.param("input", "wells.json", id="input"),
        pytest.param("multiplier", 3, id="multiplier"),
        pytest.param("default_exchange_rate", 3.41, id="default_exchange_rate"),
        pytest.param("default_discount_rate", 4.75, id="default_discount_rate"),
        pytest.param("start_date", datetime.date(2000, 12, 7), id="start_date"),
        pytest.param("end_date", datetime.date(2002, 12, 23), id="end_date"),
        pytest.param("ref_date", datetime.date(2000, 12, 9), id="ref_date"),
        pytest.param("output", "junk", id="output"),
        pytest.param("output_currency", "JK", id="output_currency"),
    ),
)
def test_bep_main_entry_point_overwrite_config(
    copy_testdata_tmpdir,
    caplog,
    option,
    value,
    economic_indicator_config,
):
    copy_testdata_tmpdir(TEST_DATA)

    with caplog.at_level(logging.INFO):
        cli._overwrite_economic_indicator_config(
            Options(
                calculation="bep",
                config=EconomicIndicatorConfig.model_validate(
                    economic_indicator_config
                ),
                **{option: value},
            ),  # type: ignore
            option,
        )

    assert (
        f"Overwrite config field with '{option}' CLI argument: {value}" in caplog.text
    )


def test_bep_main_entry_lint_ignore_overwrite_config(
    copy_testdata_tmpdir,
    caplog,
    modify_economic_config,
    build_economic_parser_patch,
):
    copy_testdata_tmpdir(TEST_DATA)
    build_economic_parser_patch(
        modify_economic_config(remove_well_costs=True), calculation="bep", lint=True
    )

    with pytest.raises(SystemExit) as e:
        cli.main_entry_point()
    assert e.value.code == 0
    assert "Overwrite config field with 'multiplier' CLI argument" not in caplog.text
    assert not pathlib.Path("test").exists()
