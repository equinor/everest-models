import logging
from datetime import datetime

logger = logging.getLogger(__name__)


def recovery_factor(
    ecl_sum,
    production_key="FOPT",
    total_volume_key="FOIP",
    start_date=None,
    end_date=None,
):
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

    start_date = start_date or ecl_sum.start_date
    end_date = end_date or ecl_sum.end_date

    if start_date < ecl_sum.start_date or end_date > ecl_sum.end_date:
        msg = (
            "The date range {} - {} exceeds the simulation time, clamping"
            "to simulation time: {} - {}"
        )
        logger.warning(
            msg.format(start_date, end_date, ecl_sum.start_date, ecl_sum.end_date)
        )

    total_volume = ecl_sum.numpy_vector(total_volume_key)[0]
    if total_volume <= 0:
        return 0

    time_range = ecl_sum.time_range(start=start_date, end=end_date, interval="1d")
    produced_volume = ecl_sum.blocked_production(production_key, time_range)
    produced_volume = sum([x for x in produced_volume])

    msg = (
        "Retrieving the recovery factor for production key: {} "
        "given a total volume key: {}, within the time range {} - {}"
    )
    logger.info(msg.format(production_key, total_volume_key, start_date, end_date))

    return produced_volume / float(total_volume)
