import datetime
import itertools
import logging
from typing import Callable, Dict, Iterable, Protocol, Tuple

from ecl.summary import EclSum
from ecl.util.util import TimeVector

from spinningjenny.jobs.fm_npv.npv_config_model import NPVConfig

logger = logging.getLogger(__name__)

__all__ = ["NPVCalculator"]


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


def _get_keywords(
    summary_keys: Iterable[str], func: Callable[[str], bool]
) -> Iterable[str]:
    if all(missing_keys := [func(key) for key in summary_keys]):
        raise AttributeError(
            f"Missing required data ({list(itertools.compress(summary_keys, missing_keys))}) in summary file."
        )
    return summary_keys


def _get_ref_date(summary_start_date: datetime.date, start_date: datetime.date):
    return (
        summary_start_date
        if not start_date or summary_start_date > start_date
        else start_date
    )


class NPVCalculator:
    def __init__(self, config: NPVConfig, summary: EclSum) -> None:
        self.config = config
        self.summary = summary
        self.keywords = _get_keywords(
            config.summary_keys, lambda key: not summary.has_key(key)
        )

    def _get_exchange_rate(self, date: datetime.date, currency: str = None) -> float:
        if currency is None:
            return self.config.default_exchange_rate
        return _get_rate(
            itertools.chain(self.config.exchange_rates.get(currency, [])),
            date,
            self.config.default_exchange_rate,
        )

    def _discount_npv(self, npv: float, date: datetime.date) -> float:
        discount_rate = _get_rate(
            self.config.discount_rates, date, self.config.default_discount_rate
        )
        return npv / (1 + discount_rate) ** ((date - self.ref_date).days / 365.25)

    def _extract_costs(self, well_dates: Dict[str, datetime.date]) -> float:
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

        return sum(self._discount_npv(*cost) for cost in get_costs())

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

    def _extract_prices(self, time_range: TimeVector) -> float:
        blocked_productions = {  # way to expensive to invoke as inline loop command
            keyword: self.summary.blocked_production(keyword, time_range)
            for keyword in self.keywords
        }
        return sum(
            self._discount_npv(
                sum(
                    blocked_productions[keyword][index] * transaction
                    for keyword in self.keywords
                    if (transaction := self._get_price(date.date(), keyword))
                    is not None
                ),
                date.date(),
            )
            for index, date in enumerate(time_range[1:])
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

    def compute(self, well_dates: Dict[str, datetime.date]) -> float:
        start_date, end_date, self.ref_date = self._get_dates()
        return round(
            (
                self._extract_prices(
                    self.summary.time_range(start_date, end_date, interval="1d")
                )
                - self._extract_costs(well_dates)
            )
            * self.config.multiplier,
            2,
        )
