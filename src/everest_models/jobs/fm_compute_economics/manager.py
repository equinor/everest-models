import datetime
import itertools
import logging
from abc import ABC, abstractmethod
from typing import Callable, Dict, Iterable, Protocol, Tuple, Union

from resdata.summary import Summary
from resdata.util.util import TimeVector

from everest_models.jobs.fm_compute_economics.economic_indicator_config_model import (
    EconomicIndicatorConfig,
)

logger = logging.getLogger(__name__)

__all__ = ["EconomicIndicatorCalculatorABC"]


CONVERTION_CUBIC_METERS_TO_BBL = 6.289814


class Rate(Protocol):
    date: datetime.date
    value: float


def _rate_sort_reverse_dates(rates: Iterable[Rate]) -> Iterable[Rate]:
    return sorted(rates, key=lambda rate: rate.date, reverse=True)


def _get_rate(rates: Iterable[Rate], date: datetime.date, default: float) -> float:
    for rate in _rate_sort_reverse_dates(rates):
        if rate.date <= date:
            return rate.value
    return default


def _get_ref_date(summary_start_date: datetime.date, start_date: datetime.date):
    return (
        summary_start_date
        if not start_date or summary_start_date > start_date
        else start_date
    )


class EclipseSummary:
    def __init__(self, config) -> None:
        self.main = self.get_summary(config.summary.main)
        self.reference = self.get_summary(config.summary.reference)
        self.keys = self.get_keys(config.summary.keys)
        self.start_date = self.main.start_date
        self.end_date = self.main.end_date
        self.time_range = self.main.time_range

    @staticmethod
    def _get_keywords(
        summary_keys: Iterable[str], func: Callable[[str], bool]
    ) -> Tuple[str]:
        if all(missing_keys := [func(key) for key in summary_keys]):
            raise AttributeError(
                f"Missing required data ({list(itertools.compress(summary_keys, missing_keys))}) in summary file."
            )
        return tuple(summary_keys)

    def get_summary(self, filepath: Union[str, None]) -> Union[Summary, None]:
        return Summary(str(filepath)) if filepath else None

    def get_keys(self, config_keys: Tuple[str, ...]) -> Tuple[str, ...]:
        main_keywords = EclipseSummary._get_keywords(
            config_keys, lambda key: not self.main.has_key(key)
        )
        reference_keywords = (
            main_keywords
            if self.reference is None
            else EclipseSummary._get_keywords(
                config_keys, lambda key: not self.reference.has_key(key)
            )
        )

        if set(main_keywords) != set(reference_keywords):
            raise AttributeError("unconsistent keys between main and reference summary")

        return main_keywords

    def get_blocked_production_main(self, time_range: TimeVector):
        block_productions = {
            keyword: self.main.blocked_production(keyword, time_range)
            for keyword in self.keys
        }
        return block_productions

    def get_blocked_production_reference(self, time_range: TimeVector):
        block_productions = {
            keyword: self.reference.blocked_production(keyword, time_range)
            for keyword in self.keys
        }
        return block_productions

    def get_delta_blocked_productions(self, time_range: TimeVector):
        blocked_productions = self.get_blocked_production_main(time_range)
        if isinstance(self.reference, Summary):
            try:
                ref_blocked_productions = self.get_blocked_production_reference(
                    time_range
                )
                blocked_productions = {
                    key: blocked_productions[key] - ref_blocked_productions[key]
                    for key in self.keys
                }
            except RuntimeError as re:
                print(re)
                print("summary and reference summary files are not consistent")
        return blocked_productions


class EconomicIndicatorCalculatorABC(ABC):
    def __init__(self, config: EconomicIndicatorConfig) -> None:
        self.config = config
        self.summary = EclipseSummary(config)

    def _get_output_exchange_rate(self, date: datetime.date) -> float:
        if self.config.output.currency_rate is None:
            return self.config.default_exchange_rate
        return _get_rate(
            itertools.chain(self.config.output.currency_rate),
            date,
            self.config.default_exchange_rate,
        )

    def _get_exchange_rate(self, date: datetime.date, currency: str = None) -> float:
        to_output = self._get_output_exchange_rate(date)
        if currency is None:
            return self.config.default_exchange_rate * to_output
        return (
            _get_rate(
                itertools.chain(self.config.exchange_rates.get(currency, [])),
                date,
                self.config.default_exchange_rate,
            )
            * to_output
        )

    def _discount(self, economic_indicator: float, date: datetime.date) -> float:
        discount_rate = _get_rate(
            self.config.discount_rates, date, self.config.default_discount_rate
        )
        return economic_indicator / (1 + discount_rate) ** (
            (date - self.ref_date).days / 365.25
        )

    def _get_dates(self) -> Tuple[datetime.date, datetime.date, datetime.date]:
        return (
            (self.summary.start_date, self.summary.end_date, self.summary.start_date)
            if not self.config.dates
            else (
                self.config.dates.start_date or self.summary.start_date,
                self.config.dates.end_date or self.summary.end_date,
                self.config.dates.ref_date
                or _get_ref_date(self.summary.start_date, self.config.dates.start_date),
            )
        )

    def _extract_discounted_costs(self, well_dates: Dict[str, datetime.date]) -> float:
        def get_costs():
            return itertools.chain(
                (
                    (
                        self._get_exchange_rate(cost.date, cost.currency) * cost.value,
                        cost.date,
                    )
                    for cost in self.config.costs
                ),
                (
                    (
                        self._get_exchange_rate(well_dates[entry.well], entry.currency)
                        * entry.value,
                        well_dates[entry.well],
                    )
                    for entry in self.config.well_costs
                    if entry.well in well_dates
                )
                if self.config.well_costs and well_dates
                else [],
            )

        return sum(self._discount(*cost) for cost in get_costs())

    @abstractmethod
    def compute(self, well_dates: Dict[str, datetime.date]) -> float:
        raise NotImplementedError


class NPVCalculator(EconomicIndicatorCalculatorABC):
    def __init__(self, config: EconomicIndicatorConfig) -> None:
        super().__init__(config)

    def _get_price(self, date: datetime.date, keyword: str) -> float:
        if keyword not in self.config.prices:
            raise AttributeError(f"Price information missing for {keyword}")

        for tariff in _rate_sort_reverse_dates(
            itertools.chain(self.config.prices[keyword]),
        ):
            if tariff.date <= date:
                return self._get_exchange_rate(date, tariff.currency) * tariff.value

        logger.warning(f"Price information missing at {date} for {keyword}.")
        return None

    def _extract_discounted_prices(self, time_range: TimeVector) -> float:
        blocked_productions = self.summary.get_delta_blocked_productions(time_range)
        return sum(
            self._discount(
                sum(
                    blocked_productions[keyword][index] * transaction
                    for keyword in self.summary.keys
                    if (transaction := self._get_price(date.date(), keyword))
                    is not None
                ),
                date.date(),
            )
            for index, date in enumerate(time_range[1:])
        )

    def compute(self, well_dates: Dict[str, datetime.date]) -> float:
        start_date, end_date, self.ref_date = self._get_dates()
        return round(
            (
                self._extract_discounted_prices(
                    self.summary.time_range(start_date, end_date, interval="1d")
                )
                - self._extract_discounted_costs(well_dates)
            )
            * self.config.multiplier,
            2,
        )


class BEPCalculator(EconomicIndicatorCalculatorABC):
    def __init__(self, config: EconomicIndicatorConfig) -> None:
        super().__init__(config)
        self.oil_equivalent = self.config.oil_equivalent

    def _get_oil_equivalent(self, blocked_productions):
        oil_equivalent = {}
        for input_phase, output_phases in self.oil_equivalent.remap.items():
            blocked_production = blocked_productions[input_phase]
            for output_phase, equivalent in output_phases.items():
                oil_equivalent[output_phase] = (
                    blocked_production
                    * equivalent
                    * self.oil_equivalent.oil[output_phase]
                    * CONVERTION_CUBIC_METERS_TO_BBL
                )
        return oil_equivalent

    def _extract_discounted_production(self, time_range: TimeVector) -> float:
        blocked_productions = self.summary.get_delta_blocked_productions(time_range)
        oil_equivalent = self._get_oil_equivalent(blocked_productions)
        return sum(
            self._discount(
                sum(
                    oil_equivalent[keyword][index]
                    for keyword in self.oil_equivalent.oil
                ),
                date.date(),
            )
            for index, date in enumerate(time_range[1:])
        )

    def compute(self, well_dates: Dict[str, datetime.date]) -> float:
        start_date, end_date, self.ref_date = self._get_dates()
        return round(
            (
                self._extract_discounted_costs(well_dates)
                / self._extract_discounted_production(
                    self.summary.time_range(start_date, end_date, interval="1d")
                )
            )
            * self.config.multiplier,
            2,
        )


# The keys of the INDICATORS dictionary should be consistent with the choices given to argparse in parser.py
INDICATORS = {"npv": NPVCalculator, "bep": BEPCalculator}


def create_indicator(calculation: str, config: EconomicIndicatorConfig) -> None:
    if calculation not in INDICATORS:
        raise ValueError(
            f"Invalid indicator: {calculation} ---  Select from {INDICATORS.keys()} "
        )

    return INDICATORS[calculation](config)
