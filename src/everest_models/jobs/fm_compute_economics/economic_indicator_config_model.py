import datetime
import logging
import pathlib
from typing import Dict, Optional, Tuple

from pydantic import Field, FilePath, ValidationError, root_validator, validator

from everest_models.jobs.fm_compute_economics.currency import CURRENCY_CODES
from everest_models.jobs.shared.models import BaseConfig, BaseFrozenConfig

logger = logging.getLogger(__name__)


class Dates(BaseConfig):
    start_date: datetime.date = None
    end_date: datetime.date = None
    ref_date: datetime.date = None


class Capital(BaseFrozenConfig):
    value: float
    currency: Optional[str] = None

    @validator("currency")
    def currency_exist(cls, currency):
        if currency is not None and currency not in CURRENCY_CODES:
            raise ValidationError("Currency does not exist")
        return currency


class CurrencyRate(Capital):
    date: datetime.date


class WellCost(Capital):
    well: str


class EclipseSummaryConfig(BaseConfig):
    main: FilePath
    reference: Optional[FilePath]
    keys: Tuple[str, ...] = Field(default_factory=tuple)


class OutputConfig(BaseConfig):
    file: pathlib.Path
    currency: Optional[str]
    currency_rate: Optional[Tuple[CurrencyRate, ...]]


class OilEquivalentConversionConfig(BaseFrozenConfig):
    oil: Dict[str, float]
    remap: Optional[Dict[str, Dict[str, float]]]


class EconomicIndicatorConfig(BaseConfig):
    prices: Dict[str, Tuple[CurrencyRate, ...]]
    summary: EclipseSummaryConfig
    multiplier: float = 1
    default_exchange_rate: float = 1
    default_discount_rate: float = 0.08
    dates: Dates = Dates()
    exchange_rates: Dict[str, Tuple[CurrencyRate, ...]] = Field(default_factory=dict)
    discount_rates: Tuple[CurrencyRate, ...] = Field(default_factory=tuple)
    costs: Tuple[CurrencyRate, ...] = Field(default_factory=tuple)
    well_costs: Tuple[WellCost, ...] = Field(default_factory=tuple)
    wells_input: Optional[FilePath]
    output: OutputConfig
    oil_equivalent: Optional[OilEquivalentConversionConfig]

    @root_validator(pre=True)
    def populate_summary_keys(cls, values):
        if isinstance(values["summary"], dict):
            if not ("keys" in values["summary"] and values["summary"]["keys"]):
                values["summary"]["keys"] = tuple(values["prices"])
        elif isinstance(values["summary"], EclipseSummaryConfig):
            if not (hasattr(values["summary"], "keys") and values["summary"].keys):
                values["summary"].keys = tuple(values["prices"])
        return values

    @root_validator(pre=True)
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

    @root_validator(pre=True)
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
                setattr(values["output"], "currency_rate", currency_rate)

        return values

    @property
    def start_date(self) -> Optional[datetime.date]:
        return self.dates.start_date

    @property
    def end_date(self) -> Optional[datetime.date]:
        return self.dates.end_date

    @property
    def ref_date(self) -> Optional[datetime.date]:
        return self.dates.ref_date
