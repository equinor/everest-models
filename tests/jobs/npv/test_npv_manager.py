import copy
import datetime

import pytest
from everest_models.jobs.fm_npv.manager import NPVCalculator
from everest_models.jobs.fm_npv.npv_config_model import NPVConfig
from everest_models.jobs.shared.validators import valid_input_file
from jobs.npv.parser import ecl_summary_npv
from sub_testdata import NPV as TEST_DATA


@pytest.fixture(scope="module")
def npv_config_dict(path_test_data):
    return valid_input_file(path_test_data / TEST_DATA / "input_data.yml")


@pytest.fixture(scope="module")
def npv_summary():
    return ecl_summary_npv()


@pytest.fixture(scope="module")
def npv_well_dates():
    return {
        "OP_4": datetime.date(2000, 2, 23),
        "OP_5": datetime.date(2000, 6, 14),
        "OP_1": datetime.date(2000, 7, 19),
    }


def test_npv_base_case(npv_config_dict, npv_summary, npv_well_dates):
    manager = NPVCalculator(
        config=NPVConfig.parse_obj(npv_config_dict), summary=npv_summary
    )
    assert manager.compute(npv_well_dates) == 691981114.68


def test_npv_base_case_no_input(npv_config_dict, npv_summary):
    manager = NPVCalculator(
        config=NPVConfig.parse_obj(npv_config_dict), summary=npv_summary
    )
    assert manager.compute({}) == 865092178.9


def test_npv_base_case_omit_dates_summary_keys(
    npv_config_dict, npv_summary, npv_well_dates
):
    config_dict = copy.deepcopy(npv_config_dict)
    config_dict.pop("dates")
    config_dict.pop("summary_keys")

    manager = NPVCalculator(
        config=NPVConfig.parse_obj(config_dict), summary=npv_summary
    )
    assert manager.compute(npv_well_dates) == 1323951495.03


def test_npv_base_case_modify_multiplier(npv_config_dict, npv_summary, npv_well_dates):
    config_dict = copy.deepcopy(npv_config_dict)
    config_dict.pop("dates")
    config_dict.pop("summary_keys")
    config_dict["multiplier"] = 2

    manager = NPVCalculator(
        config=NPVConfig.parse_obj(config_dict), summary=npv_summary
    )
    assert manager.compute(npv_well_dates) == 2647902990.07


def test_npv_base_case_modify_ref_date(npv_config_dict, npv_summary, npv_well_dates):
    config_dict = copy.deepcopy(npv_config_dict)
    config_dict.pop("summary_keys")
    dates = config_dict["dates"]
    dates.pop("start_date")
    dates.pop("end_date")
    dates["ref_date"] = datetime.date(2000, 5, 6)

    manager = NPVCalculator(
        config=NPVConfig.parse_obj(config_dict), summary=npv_summary
    )
    assert manager.compute(npv_well_dates) == 1344403927.71


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
def test_npv_base_case_modify_start_end_dates(
    dates, pop_keys, expected, npv_config_dict, npv_summary, npv_well_dates
):
    config_dict = copy.deepcopy(npv_config_dict)
    if pop_keys:
        config_dict.pop("summary_keys")
    config_dates = config_dict["dates"]
    config_dates.pop("ref_date")
    config_dates.update(dates)

    manager = NPVCalculator(
        config=NPVConfig.parse_obj(config_dict), summary=npv_summary
    )
    assert manager.compute(npv_well_dates) == expected


def test_npv_summary_keys_not_available(npv_config_dict, npv_summary):
    config_dict = copy.deepcopy(npv_config_dict)
    config_dict["summary_keys"] = ["NOT_EXISTING", "FAULTY_KEY"]

    with pytest.raises(AttributeError) as e:
        NPVCalculator(NPVConfig.parse_obj(config_dict), npv_summary)

    assert (
        "Missing required data (['NOT_EXISTING', 'FAULTY_KEY']) in summary file."
        in str(e.value)
    )
