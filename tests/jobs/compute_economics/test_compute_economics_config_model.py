import pathlib

import pytest
from everest_models.jobs.fm_compute_economics.economic_indicator_config_model import (
    Capital,
    EconomicIndicatorConfig,
    OutputConfig,
)
from pydantic import ValidationError


def test_economic_indicator_config_defaults():
    config = EconomicIndicatorConfig.model_validate(
        {
            "summary": {
                "main": "tests/jobs/compute_economics/test_compute_economics_config_model.py",
            },
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
            "output": {"file": "test_0", "currency": "USD"},
        }
    )

    assert config.multiplier == 1
    assert config.default_discount_rate == 0.08
    assert config.default_exchange_rate == 1
    assert config.summary.keys == ("FOPT",)
    assert config.start_date is None
    assert config.end_date is None
    assert config.ref_date is None
    assert not config.discount_rates and isinstance(config.discount_rates, tuple)
    assert not config.well_costs and isinstance(config.well_costs, tuple)
    assert isinstance(config.output, OutputConfig)
    assert config.output.file == pathlib.Path("test_0")
    assert config.output.currency == "USD"


def test_economic_indicator_money_bad_currency():
    with pytest.raises(ValidationError):
        Capital.model_validate({"value": 3.14, "currency": "PIE"})
