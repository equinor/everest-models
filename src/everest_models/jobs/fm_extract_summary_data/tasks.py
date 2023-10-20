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
    """Extract interpreted eclipse summary value for given key and end date.

    Args:
        summary (EclSum): eclipse summary
        key (str): eclipse summary key
        end_date (datetime.date): summary key interval end date

    Returns:
        float: interpreted value
    """
    return summary.get_interp(key, date=end_date)


def _extract_max(
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


def _extract_diff(
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
            return _extract_max(summary, key, start_date, end_date)
        if self == self.DIFF:
            return _extract_diff(summary, key, start_date, end_date)

    @classmethod
    def types(cls):
        return tuple(el.value for el in cls)


def validate_arguments(options: argparse.Namespace) -> argparse.Namespace:
    """Validate that given arguments in Namespace are valid.

    Compare standalone argument values to eclipse summary data

    Args:
        options (argparse.Namespace): Program session context

    Raises:
        argparse.ArgumentTypeError: If any argument value fails validation

    Returns:
        argparse.Namespace: Program session context
    """
    errors = []
    available_dates = [d.date() for d in options.summary.dates]

    if options.key not in options.summary:
        errors.append(f"Missing required data {options.key} in summary file.")
    if options.start_date is not None:
        if options.start_date > options.end_date:
            errors.append(
                f"Start date '{options.start_date}' is after end date '{options.end_date}'."
            )
        if options.start_date not in available_dates:
            errors.append(
                f"Start date '{options.start_date}' is not part of the simulation report dates"
            )
    if options.end_date not in available_dates:
        errors.append(
            f"End date '{options.end_date}' is not part of the simulation report dates"
        )
    if errors:
        raise argparse.ArgumentTypeError("\n".join(errors))
    return options
