import pytest
from pydantic import ValidationError

from everest_models.jobs.fm_npv.npv_config import NPVConfig


def test_npv_config_summary_keys():
    config = NPVConfig.model_validate(
        {
            "prices": {
                "FOPT": [
                    {"date": "1999-01-01", "value": 60, "currency": "USD"},
                ],
            },
        }
    )
    assert config.summary_keys == ("FOPT",)


def test_npv_config_summary_keys_missing_prices():
    with pytest.raises(
        ValidationError, match="Both summary_keys and prices keys missing"
    ):
        NPVConfig.model_validate({})


def test_npv_config_well_costs_missing_values():
    with pytest.raises(
        ValidationError,
        match="Exactly one type of well cost must be set for each well",
    ):
        NPVConfig.model_validate(
            {
                "prices": {
                    "FOPT": [{"date": "1999-01-01", "value": 60, "currency": "USD"}]
                },
                "well_costs": [{"well": "OP_2"}],
            }
        )


def test_npv_config_well_costs_not_exclusive_values():
    with pytest.raises(
        ValidationError,
        match="Exactly one type of well cost must be set for each well",
    ):
        NPVConfig.model_validate(
            {
                "prices": {
                    "FOPT": [{"date": "1999-01-01", "value": 60, "currency": "USD"}],
                },
                "well_costs": [
                    {
                        "well": "OP_1",
                        "value": 10000000,
                        "currency": "USD",
                        "value_per_km": 5000000,
                    },
                ],
            }
        )
