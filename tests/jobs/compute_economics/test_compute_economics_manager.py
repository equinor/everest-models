import copy
import datetime
from unittest.mock import patch

import pytest
from everest_models.jobs.fm_compute_economics.economic_indicator_config_model import (
    EconomicIndicatorConfig,
)
from everest_models.jobs.fm_compute_economics.manager import NPVCalculator
from everest_models.jobs.shared.validators import valid_input_file
from jobs.compute_economics.parser import (
    ecl_reference_summary_economic_indicator,
    ecl_reference_summary_economic_indicator_not_consistent,
    ecl_summary_economic_indicator,
)
from sub_testdata import ECONOMIC_INDICATOR as TEST_DATA


@pytest.fixture(scope="module")
def economic_indicator_input_dict(path_test_data):
    return valid_input_file(path_test_data / TEST_DATA / "input_data.yml")


@pytest.fixture(scope="module")
def economic_indicator_summary():
    return ecl_summary_economic_indicator()


@pytest.fixture(scope="module")
def economic_indicator_reference_summary():
    return ecl_reference_summary_economic_indicator()


@pytest.fixture(scope="module")
def economic_indicator_reference_summary_not_consistent():
    return ecl_reference_summary_economic_indicator_not_consistent()


@pytest.fixture(scope="module")
def economic_indicator_well_dates():
    return {
        "OP_4": datetime.date(2000, 2, 23),
        "OP_5": datetime.date(2000, 6, 14),
        "OP_1": datetime.date(2000, 7, 19),
    }


@patch("everest_models.jobs.fm_compute_economics.manager.EclipseSummary.get_summary")
def test_npv_base_case(
    mocker,
    copy_testdata_tmpdir,
    economic_indicator_input_dict,
    economic_indicator_summary,
    economic_indicator_well_dates,
):
    copy_testdata_tmpdir(TEST_DATA)

    config = copy.deepcopy(economic_indicator_input_dict)
    mocker.side_effect = [economic_indicator_summary, None]
    manager = NPVCalculator(
        config=EconomicIndicatorConfig.parse_obj(config),
    )
    assert manager.compute(economic_indicator_well_dates) == 691981114.68


@patch("everest_models.jobs.fm_compute_economics.manager.EclipseSummary.get_summary")
def test_npv_base_case_with_reference_summary(
    mocker,
    copy_testdata_tmpdir,
    economic_indicator_input_dict,
    economic_indicator_summary,
    economic_indicator_reference_summary,
    economic_indicator_well_dates,
):
    copy_testdata_tmpdir(TEST_DATA)

    config = copy.deepcopy(economic_indicator_input_dict)
    mocker.side_effect = [
        economic_indicator_summary,
        economic_indicator_reference_summary,
    ]
    # The test checks that the value is the one obtained at the first version of the function
    # It has been checked that this corresponds to the difference of production (FOPT) between the two EclSum data
    manager = NPVCalculator(
        config=EconomicIndicatorConfig.parse_obj(config),
    )
    assert manager.compute(economic_indicator_well_dates) == 156999155.17


@patch("everest_models.jobs.fm_compute_economics.manager.EclipseSummary.get_summary")
def test_npv_base_case_with_reference_summary_failing(
    mocker,
    copy_testdata_tmpdir,
    economic_indicator_input_dict,
    economic_indicator_summary,
    economic_indicator_reference_summary_not_consistent,
    economic_indicator_well_dates,
):
    copy_testdata_tmpdir(TEST_DATA)

    config = copy.deepcopy(economic_indicator_input_dict)
    mocker.side_effect = [
        economic_indicator_summary,
        economic_indicator_reference_summary_not_consistent,
    ]
    manager = NPVCalculator(
        config=EconomicIndicatorConfig.parse_obj(config),
    )
    with pytest.raises(Exception) as exc_info:
        manager.compute(economic_indicator_well_dates)
    assert str(exc_info.value) == "'Summary case does not have key:FOPT'"


@patch("everest_models.jobs.fm_compute_economics.manager.EclipseSummary.get_summary")
def test_npv_base_case_no_input(
    mocker,
    copy_testdata_tmpdir,
    economic_indicator_input_dict,
    economic_indicator_summary,
):
    copy_testdata_tmpdir(TEST_DATA)

    config = copy.deepcopy(economic_indicator_input_dict)
    mocker.side_effect = [economic_indicator_summary, None]
    manager = NPVCalculator(
        config=EconomicIndicatorConfig.parse_obj(config),
    )
    assert manager.compute({}) == 865092178.9


@patch("everest_models.jobs.fm_compute_economics.manager.EclipseSummary.get_summary")
def test_npv_base_case_omit_dates_summary_keys(
    mocker,
    copy_testdata_tmpdir,
    economic_indicator_input_dict,
    economic_indicator_summary,
    economic_indicator_well_dates,
):
    copy_testdata_tmpdir(TEST_DATA)

    config = copy.deepcopy(economic_indicator_input_dict)
    config.pop("dates")
    config["summary"].pop("keys")
    mocker.side_effect = [economic_indicator_summary, None]

    manager = NPVCalculator(
        config=EconomicIndicatorConfig.parse_obj(config),
    )
    assert manager.compute(economic_indicator_well_dates) == 1323951495.03


@patch("everest_models.jobs.fm_compute_economics.manager.EclipseSummary.get_summary")
def test_npv_base_case_modify_multiplier(
    mocker,
    copy_testdata_tmpdir,
    economic_indicator_input_dict,
    economic_indicator_summary,
    economic_indicator_well_dates,
):
    copy_testdata_tmpdir(TEST_DATA)

    config = copy.deepcopy(economic_indicator_input_dict)
    config.pop("dates")
    config["summary"].pop("keys")
    config["multiplier"] = 2
    mocker.side_effect = [economic_indicator_summary, None]

    manager = NPVCalculator(
        config=EconomicIndicatorConfig.parse_obj(config),
    )
    assert manager.compute(economic_indicator_well_dates) == 2647902990.07


@patch("everest_models.jobs.fm_compute_economics.manager.EclipseSummary.get_summary")
def test_npv_base_case_modify_ref_date(
    mocker,
    copy_testdata_tmpdir,
    economic_indicator_input_dict,
    economic_indicator_summary,
    economic_indicator_well_dates,
):
    copy_testdata_tmpdir(TEST_DATA)

    config = copy.deepcopy(economic_indicator_input_dict)
    config["summary"].pop("keys")
    dates = config["dates"]
    dates.pop("start_date")
    dates.pop("end_date")
    dates["ref_date"] = datetime.date(2000, 5, 6)
    mocker.side_effect = [economic_indicator_summary, None]

    manager = NPVCalculator(
        config=EconomicIndicatorConfig.parse_obj(config),
    )
    assert manager.compute(economic_indicator_well_dates) == 1344403927.71


@pytest.mark.parametrize(
    "dates, pop_keys, expected",
    (
        pytest.param(
            {
                "start_date": datetime.date(1999, 12, 1),
                "end_date": datetime.date(1999, 12, 2),
            },
            True,
            -369456947.15,
            id="one_day",
        ),
        pytest.param(
            {
                "start_date": datetime.date(1999, 12, 1),
                "end_date": datetime.date(2003, 1, 1),
            },
            True,
            1165564342.70,
            id="long_period",
        ),
        pytest.param(
            {
                "start_date": datetime.date(2000, 6, 12),
                "end_date": datetime.date(2002, 12, 23),
            },
            False,
            923994410.31,
            id="common",
        ),
        pytest.param(
            {
                "start_date": datetime.date(1998, 11, 30),
                "end_date": datetime.date(2005, 1, 2),
            },
            True,
            1323951495.03,
            id="outside_summary_dates",
        ),
    ),
)
@patch("everest_models.jobs.fm_compute_economics.manager.EclipseSummary.get_summary")
def test_npv_base_case_modify_start_end_dates(
    mocker,
    copy_testdata_tmpdir,
    dates,
    pop_keys,
    expected,
    economic_indicator_input_dict,
    economic_indicator_summary,
    economic_indicator_well_dates,
):
    copy_testdata_tmpdir(TEST_DATA)

    config = copy.deepcopy(economic_indicator_input_dict)
    if pop_keys:
        config["summary"].pop("keys")
    config_dates = config["dates"]
    config_dates.pop("ref_date")
    config_dates.update(dates)
    mocker.side_effect = [economic_indicator_summary, None]

    manager = NPVCalculator(
        config=EconomicIndicatorConfig.parse_obj(config),
    )
    assert manager.compute(economic_indicator_well_dates) == expected


@patch("everest_models.jobs.fm_compute_economics.manager.EclipseSummary.get_summary")
def test_npv_summary_keys_not_available(
    mocker,
    copy_testdata_tmpdir,
    economic_indicator_input_dict,
    economic_indicator_summary,
):
    copy_testdata_tmpdir(TEST_DATA)

    config = copy.deepcopy(economic_indicator_input_dict)
    mocker.side_effect = [economic_indicator_summary, None]
    config["summary"]["keys"] = ["NOT_EXISTING", "FAULTY_KEY"]
    config_ = EconomicIndicatorConfig.parse_obj(config)

    with pytest.raises(AttributeError) as e:
        NPVCalculator(config_)

    assert (
        "Missing required data (['NOT_EXISTING', 'FAULTY_KEY']) in summary file."
        in str(e.value)
    )
