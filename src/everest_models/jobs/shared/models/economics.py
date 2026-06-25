from datetime import date
from typing import Annotated, Self

from pydantic import AfterValidator, ConfigDict, Field, model_validator

from ..currency import currency_exist
from .base_config import ModelConfig

__all__ = ["Dates", "CurrencyRate", "WellCost"]


class Dates(ModelConfig):
    model_config = ConfigDict(frozen=False)

    start_date: Annotated[date, Field(default=None, description="")]
    end_date: Annotated[date, Field(default=None, description="")]
    ref_date: Annotated[date, Field(default=None, description="")]


class CurrencyRate(ModelConfig):
    date: Annotated[date, Field(description="")]
    value: Annotated[float, Field(description="")]
    currency: Annotated[
        str,
        AfterValidator(currency_exist),
        Field(default=None, description=""),
    ]


class WellCost(ModelConfig):
    well: Annotated[str, Field(description="Well name")]
    value: Annotated[
        float | None,
        Field(
            default=None,
            description="Total cost per well (mutually exclusive with value_per_km)",
        ),
    ]
    currency: Annotated[
        str,
        AfterValidator(currency_exist),
        Field(default=None, description=""),
    ]
    value_per_km: Annotated[
        float | None,
        Field(
            default=None, description="Well cost per km (mutually exclusive with value)"
        ),
    ]

    @model_validator(mode="after")
    def ensure_value_is_mutually_exclusive_with_value_per_km(self) -> Self:
        if (self.value is not None and self.value_per_km is not None) or (
            self.value is None and self.value_per_km is None
        ):
            raise ValueError(
                "Exactly one type of well cost must be set for each well. "
                "Set either 'value' or 'value_per_km'."
            )
        return self


class EconomicConfig(ModelConfig):
    model_config = ConfigDict(frozen=False, validate_assignment=True)

    prices: Annotated[dict[str, tuple[CurrencyRate, ...]], Field(description="")]
    multiplier: Annotated[
        float,
        Field(default=1, description=""),
    ]
    default_exchange_rate: Annotated[float, Field(default=1, description="")]
    default_discount_rate: Annotated[float, Field(default=0.08, description="")]
    dates: Annotated[Dates, Field(default_factory=lambda: Dates(**{}), description="")]
    exchange_rates: Annotated[
        dict[str, tuple[CurrencyRate, ...]], Field(default_factory=dict, description="")
    ]
    discount_rates: Annotated[
        tuple[CurrencyRate, ...], Field(default_factory=tuple, description="")
    ]
    costs: Annotated[
        tuple[CurrencyRate, ...], Field(default_factory=tuple, description="")
    ]
    well_costs: Annotated[
        tuple[WellCost, ...], Field(default_factory=tuple, description="")
    ]

    @property
    def start_date(self) -> date | None:
        return self.dates.start_date

    @property
    def end_date(self) -> date | None:
        return self.dates.end_date

    @property
    def ref_date(self) -> date | None:
        return self.dates.ref_date
