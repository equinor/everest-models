import datetime
import logging
from typing import Tuple

from resdata.summary import Summary

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
    summary: Summary,
    start_date: datetime.date,
    end_date: datetime.date,
    production_key: str,
    total_volume_key: str,
) -> float:
    """Given summary keys and dates, calculate recovery factor.

    - Keys given must be present in the eclipse summary file.
    - If dates are outside simulation range, they will be clamped to the nearest summary date.
    - An error occurs if the entire date range is outside simulation range.

    Args:
        summary (Summary): Eclipse summary
        start_date (datetime.date): First date in the summary
        end_date (datetime.date): Last date in the summary
        production_key (str, optional): A valid summary key.
        total_volume_key (str, optional): A valid summary key.

    Returns:
        float: The fraction of fluid recovered
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
