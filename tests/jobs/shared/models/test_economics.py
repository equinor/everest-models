import pytest
from pydantic import ValidationError

from everest_models.jobs.shared.models.economics import EconomicConfig, _Capital


def test_economic_currency_bad():
    with pytest.raises(ValidationError, match=r"Currency PIE not in supported \[.*\]"):
        _Capital.model_validate({"value": 3.14, "currency": "PIE"})


def test_economic_config_defaults():
    config = EconomicConfig.model_validate(
        {
            "prices": {
                "FOPT": [
                    {"date": "1999-01-01", "value": 60, "currency": "USD"},
                ],
            },
            "exchange_rates": {"USD": [{"date": "1997-01-01", "value": 5}]},
            "costs": [
                {
                    "date": "1999-01-01",
                    "value": 10000000,
                    "currency": "USD",
                },
                {"date": "1999-10-01", "value": 20000000},
            ],
        }
    )

    assert config.multiplier == 1
    assert config.default_discount_rate == 0.08
    assert config.default_exchange_rate == 1
    assert config.start_date is None
    assert config.end_date is None
    assert config.ref_date is None
    assert not config.discount_rates and isinstance(config.discount_rates, tuple)
    assert not config.well_costs and isinstance(config.well_costs, tuple)
