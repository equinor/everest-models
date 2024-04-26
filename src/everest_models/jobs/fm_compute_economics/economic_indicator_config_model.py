import logging
import pathlib
from typing import Any, Dict, Tuple

from pydantic import ConfigDict, Field, FilePath, NewPath, model_validator
from typing_extensions import Annotated

from everest_models.jobs.shared.currency import CURRENCY_CODES
from everest_models.jobs.shared.models import ModelConfig
from everest_models.jobs.shared.models.economics import CurrencyRate, EconomicConfig

logger = logging.getLogger(__name__)


def get(obj, key, default=None):
    if isinstance(obj, Dict):
        return obj.get(key, default)
    else:
        return getattr(obj, key, default)


def set(obj, key, value):
    if isinstance(obj, Dict):
        obj[key] = value
    else:
        setattr(obj, key, value)
    return obj


def has_and_not_empty(obj, key):
    if isinstance(obj, Dict):
        return key in obj and bool(obj[key])
    else:
        return hasattr(obj, key) and bool(getattr(obj, key))


class EclipseSummaryConfig(ModelConfig):
    model_config = ConfigDict(frozen=False)
    main: Annotated[pathlib.Path, Field(description="", frozen=True)]
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
    @classmethod
    def populate_summary_keys(cls, values: Dict[str, Any]):
        if not has_and_not_empty(values["summary"], "keys"):
            set(values["summary"], "keys", tuple(values["prices"]))
        return values

    @model_validator(mode="before")
    @classmethod
    def currency_exist(cls, values):
        if get(values["output"], "currency", default=None) is None:
            return values
        if get(values["output"], "currency") not in CURRENCY_CODES:
            raise ValueError(
                f"Currency {get(values['output'], 'currency')} does not exist"
            )
        if (
            "exchange_rates" in values
            and get(values["output"], "currency") not in values["exchange_rates"]
        ):
            raise ValueError("Currency cannot be interpreted from given exchange rate")
        return values

    @model_validator(mode="before")
    @classmethod
    def currency_rate_exist(cls, values):
        if get(values["output"], "currency", default=None) is None:
            return values
        if has_and_not_empty(values["output"], "currency_rate"):
            return values
        if get(values, "exchange_rates", default=None) is None:
            set(values["output"], "currency_rate", None)
        else:
            set(
                values["output"],
                "currency_rate",
                tuple(
                    {"date": rate["date"], "value": 1.0 / rate["value"]}
                    for rate in values["exchange_rates"][
                        get(values["output"], "currency")
                    ]
                ),
            )

        return values
