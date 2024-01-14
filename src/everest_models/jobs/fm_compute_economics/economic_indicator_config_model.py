import logging
import pathlib
from typing import Any, Dict, Tuple

from pydantic import ConfigDict, Field, FilePath, NewPath, model_validator
from typing_extensions import Annotated

from everest_models.jobs.shared.currency import CURRENCY_CODES
from everest_models.jobs.shared.models import ModelConfig
from everest_models.jobs.shared.models.economics import CurrencyRate, EconomicConfig

logger = logging.getLogger(__name__)


class EclipseSummaryConfig(ModelConfig):
    main: Annotated[pathlib.Path, Field(description="")]
    reference: Annotated[FilePath, Field(default=None, description="")]
    keys: Annotated[Tuple[str, ...], Field(default_factory=tuple, description="")]


class OutputConfig(ModelConfig):
    model_config = ConfigDict(frozen=False)
    file: Annotated[NewPath, Field(description="")]
    currency: Annotated[str, Field(default=None, description="")]
    currency_rate: Annotated[
        Tuple[CurrencyRate, ...], Field(default=None, description="")
    ]


class OilEquivalentConversionConfig(ModelConfig):
    oil: Annotated[Dict[str, float], Field(description="")]
    remap: Annotated[Dict[str, Dict[str, float]], Field(default=None, description="")]


class EconomicIndicatorConfig(EconomicConfig):
    summary: Annotated[EclipseSummaryConfig, Field(description="")]
    wells_input: Annotated[FilePath, Field(default=None, description="")]
    output: Annotated[OutputConfig, Field(description="")]
    oil_equivalent: Annotated[
        OilEquivalentConversionConfig, Field(default=None, description="")
    ]

    @model_validator(mode="before")
    def populate_summary_keys(cls, values: Dict[str, Any]):
        # values.setdefault("summary", {})
        # values["summary"].setdefault("keys", tuple(values.get("prices", {})))
        if isinstance(values["summary"], dict):
            if not ("keys" in values["summary"] and values["summary"]["keys"]):
                values["summary"]["keys"] = tuple(values["prices"])
        elif isinstance(values["summary"], EclipseSummaryConfig):
            if not (hasattr(values["summary"], "keys") and values["summary"].keys):
                values["summary"].keys = tuple(values["prices"])
        return values

    @model_validator(mode="before")
    @classmethod
    def currency_exist(cls, values):
        if isinstance(values["output"], dict):
            if values["output"].get("currency", None) is None:
                return values
            if values["output"]["currency"] not in CURRENCY_CODES:
                raise ValueError("Currency does not exist")
            if (
                "exchange_rates" in values
                and values["output"]["currency"] not in values["exchange_rates"]
            ):
                raise ValueError(
                    "Currency cannot be interpreted from given exchange rate"
                )
        elif isinstance(values["output"], OutputConfig):
            if not values["output"].currency:
                return values
            if values["output"].currency not in CURRENCY_CODES:
                raise ValueError("Currency does not exist")
            if (
                "exchange_rates" in values
                and values["output"].currency not in values["exchange_rates"]
            ):
                raise ValueError(
                    "Currency cannot be interpreted from given exchange rate"
                )
        return values

    @model_validator(mode="before")
    @classmethod
    def currency_rate_exist(cls, values):
        if isinstance(values["output"], dict):
            if values["output"].get("currency", None) is None:
                return values
            if (
                "currency_rate" in values["output"]
                and values["output"]["currency_rate"]
            ):
                return values
            if values.get("exchange_rates", None) is None:
                values["output"]["currency_rate"] = None
            else:
                values["output"]["currency_rate"] = tuple(
                    {"date": rate["date"], "value": 1.0 / rate["value"]}
                    for rate in values["exchange_rates"][values["output"]["currency"]]
                )
        elif isinstance(values["output"], OutputConfig):
            if not values["output"].currency:
                return values
            if (
                hasattr(values["output"], "currency_rate")
                and values["output"].currency_rate
            ):
                return values
            if values.get("exchange_rates", None) is None:
                values["output"]["currency_rate"] = None
            else:
                currency_rate = tuple(
                    {"date": rate.date, "value": 1.0 / rate.value}
                    for rate in values["exchange_rates"][values["output"].currency]
                )
                values["output"].currency_rate = currency_rate

        return values
