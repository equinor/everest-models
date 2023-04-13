import datetime
import logging
from typing import Tuple

from ecl.summary import EclSum

logger = logging.getLogger(__name__)


def _evaluate_dates(
    user_start_date: datetime.date,
    user_end_date: datetime.date,
    ecl_start_date: datetime.date,
    ecl_end_date: datetime.date,
) -> Tuple[datetime.date, datetime.date]:
    start_date = user_start_date or ecl_start_date
    end_date = user_end_date or ecl_end_date

    if start_date < ecl_start_date or end_date > ecl_end_date:
        logger.warning(
            f"The date range {start_date} - {end_date} exceeds the simulation time, "
            f"clamping to simulation time: {ecl_start_date} - {ecl_end_date}"
        )

    return start_date, end_date


def recovery_factor(
    summary: EclSum,
    start_date: datetime.date,
    end_date: datetime.date,
    production_key: str = None,
    total_volume_key: str = None,
) -> float:
    """
    Calculates the recovery factor given summary keys and dates.
    Requires an EclSum instance to retrieve the volumes from. The summary
    keys requested must be in the EclSum instance. If the dates are outside
    the simulation range, they will be clamped to nearest. Will throw an
    error if the entire date range is outside the simulation range.

    It is up to the caller to use sane combinations of summary keys.

    Parameters
    ----------
    ecl_sum : <EclSum>
        An EclSum instance
    production_key : <string>
        A valid summary key.
        Default: FOPT
    total_volume_key : <string>
        A valid summary key.
        Default: FOIP
    start_date: <datetime.date>
        A datetime.date object.
        Default: First date in the summary
    end_date: <datetime.date>
        A datetime.date object.
        Default: Last date in the summary

    Returns:
    ----------
    float
        The fraction of fluid recovered

    """
    start_date, end_date = _evaluate_dates(
        start_date, end_date, summary.start_date, summary.end_date
    )

    if (total_volume := summary.numpy_vector(total_volume_key)[0]) <= 0:
        return 0

    produced_volume = sum(
        list(
            summary.blocked_production(
                production_key,
                timeRange=summary.time_range(
                    start=start_date, end=end_date, interval="1d"
                ),
            )
        )
    )

    logger.info(
        f"Retrieving the recovery factor for production key: {production_key} "
        f"given a total volume key: {total_volume_key}, within the time range {start_date} - {end_date}"
    )
    return produced_volume / total_volume
