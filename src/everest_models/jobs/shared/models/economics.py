from datetime import date
from typing import Dict, Optional, Tuple

from pydantic import AfterValidator, ConfigDict, Field, model_validator
from pydantic_core import PydanticCustomError
from typing_extensions import Annotated

from ..currency import currency_exist
from .base_config import ModelConfig

__all__ = ["Dates", "CurrencyRate", "WellCost"]


class Dates(ModelConfig):
    model_config = ConfigDict(frozen=False)

    start_date: Annotated[date, Field(default=None, description="")]
    end_date: Annotated[date, Field(default=None, description="")]
    ref_date: Annotated[date, Field(default=None, description="")]


class _Capital(ModelConfig):
    value: Annotated[float, Field(description="")]
    currency: Annotated[
        str,
        AfterValidator(currency_exist),
        Field(default=None, description=""),
    ]


class CurrencyRate(_Capital):
    date: Annotated[date, Field(description="")]


class WellCost(ModelConfig):
    well: Annotated[str, Field(description="Well name")]
    value: Annotated[
        Optional[float],
        Field(default=None, description="Total cost per well")
    ]
    currency: Annotated[
        str,
        AfterValidator(currency_exist),
        Field(default=None, description=""),
    ]
    value_per_km: Annotated[
        Optional[float],
        Field(default=None, description="(optional) Well cost per km")
    ]

    @model_validator(mode="after")
    def check_mutually_exclusive(self) -> "WellCost":
        if self.value is not None and self.value_per_km is not None:
            raise ValueError(
                "Only one type of well cost can be set for each well."
                "Set either 'value' or 'value_per_km', not both."
            )
    
    @model_validator(mode="after")
    def check_at_least_one_well_cost_is_set(self) -> "WellCost":
        if self.value is None and self.value_per_km is None:
            raise ValueError(
                "Exactly one type of well cost must be set for each well."
                "Set either 'value' or 'value_per_km'."
            )


class EconomicConfig(ModelConfig):
    model_config = ConfigDict(frozen=False, validate_assignment=True)

    prices: Annotated[Dict[str, Tuple[CurrencyRate, ...]], Field(description="")]
    multiplier: Annotated[
        float,
        Field(default=1, description=""),
    ]
    default_exchange_rate: Annotated[float, Field(default=1, description="")]
    default_discount_rate: Annotated[float, Field(default=0.08, description="")]
    dates: Annotated[Dates, Field(default_factory=lambda: Dates(**{}), description="")]
    exchange_rates: Annotated[
        Dict[str, Tuple[CurrencyRate, ...]], Field(default_factory=dict, description="")
    ]
    discount_rates: Annotated[
        Tuple[CurrencyRate, ...], Field(default_factory=tuple, description="")
    ]
    costs: Annotated[
        Tuple[CurrencyRate, ...], Field(default_factory=tuple, description="")
    ]
    well_costs: Annotated[
        Tuple[WellCost, ...], Field(default_factory=tuple, description="")
    ]

    @property
    def start_date(self) -> Optional[date]:
        return self.dates.start_date

    @property
    def end_date(self) -> Optional[date]:
        return self.dates.end_date

    @property
    def ref_date(self) -> Optional[date]:
        return self.dates.ref_date
