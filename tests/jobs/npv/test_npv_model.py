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
