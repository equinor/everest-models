import argparse
import datetime
import logging
from enum import Enum

import numpy as np
from ecl.summary import EclSum

logger = logging.getLogger(__name__)


def extract_value(
    summary: EclSum, key: str, end_date: datetime.date, **kwargs
) -> float:
    return summary.get_interp(key, date=end_date)


def extract_max(
    summary: EclSum, key: str, start_date: datetime.date, end_date: datetime.date
) -> float:
    return np.max(
        summary.numpy_vector(
            key,
            time_index=summary.time_range(
                start=start_date, end=end_date, interval="1d"
            ),
        )
    )


def extract_diff(
    summary: EclSum, key: str, start_date: datetime.date, end_date: datetime.date
) -> float:
    return summary.get_interp(key, date=end_date) - summary.get_interp(
        key, date=start_date
    )


class CalculationType(Enum):
    MAX = "max"
    DIFF = "diff"

    def __eq__(self, other):
        return self.value == other

    def extract(
        self,
        summary: EclSum,
        key: str,
        start_date: datetime.date,
        end_date: datetime.date,
    ) -> float:
        if self == self.MAX:
            return extract_max(summary, key, start_date, end_date)
        if self == self.DIFF:
            return extract_diff(summary, key, start_date, end_date)

    @classmethod
    def types(cls):
        return tuple(el.value for el in cls)


def validate_arguments(options: argparse.Namespace) -> argparse.Namespace:
    errors = []
    if options.key not in options.summary:
        errors.append(f"Missing required data {options.key} in summary file.")
    if options.start_date is not None and options.start_date > options.end_date:
        errors.append(
            f"Start date '{options.start_date}' is after end date '{options.end_date}'."
        )
    if not (
        options.start_date is None or options.start_date in options.summary.report_dates
    ):
        errors.append(
            f"Start date '{options.start_date}' is not part of the simulation report dates"
        )
    if options.end_date not in options.summary.report_dates:
        errors.append(
            f"End date '{options.end_date}' is not part of the simulation report dates"
        )
    if errors:
        raise argparse.ArgumentTypeError("\n".join(errors))
    return options
