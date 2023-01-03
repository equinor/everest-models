import datetime
import logging
from typing import Dict, Optional, Tuple

from pydantic import Field, ValidationError, root_validator, validator

from spinningjenny.jobs.fm_npv.currency import CURRENCY_CODES
from spinningjenny.jobs.shared.models import BaseConfig, BaseFrozenConfig

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


class NPVConfig(BaseConfig):
    prices: Dict[str, Tuple[CurrencyRate, ...]]
    exchange_rates: Dict[str, Tuple[CurrencyRate, ...]]
    costs: Tuple[CurrencyRate, ...]
    summary_keys: Tuple[str, ...]
    multiplier: float = 1
    default_exchange_rate: float = 1
    default_discount_rate: float = 0.08
    dates: Dates = Dates()
    discount_rates: Tuple[CurrencyRate, ...] = Field(default_factory=tuple)
    well_costs: Tuple[WellCost, ...] = Field(default_factory=tuple)

    @root_validator(pre=True)
    def populate_summary_keys(cls, values):
        if not ("summary_keys" in values and values["summary_keys"]):
            values["summary_keys"] = tuple(values["prices"])
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
