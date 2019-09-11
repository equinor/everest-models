from enum import Enum
import numpy as np

from spinningjenny import customized_logger

logger = customized_logger.get_logger(__name__)


class CalculationType(Enum):
    MAX = "max"
    MEAN = "mean"
    MEDIAN = "median"
    PERCENTILE = "percentile"
    CUMULATIVE = "cumulative"

    def __eq__(self, other):
        return self.value == other

    @staticmethod
    def types():
        return [el.value.lower() for el in CalculationType]


def valid_percentile(percent, parser):
    try:
        p = float(percent)
    except ValueError:
        parser.error("Invalid percentile value provided '{}'".format(percent))
    else:
        if not 0 <= p <= 100:
            parser.error("Percentile value {} not in range [0,100]".format(p))
        return float(p)


def validate_arguments(options, parser):
    summary = options.summary
    if options.key not in summary:
        parser.error("Missing required data {} in summary file.".format(options.key))

    if options.start_date:
        if options.start_date > options.end_date:
            parser.error("Start date is after end date.")

        if not summary.check_sim_time(options.start_date):
            parser.error(
                "Start date {} is not in the simulation time interval [{}, {}]".format(
                    options.start_date, summary.start_date, summary.end_date
                )
            )
    else:
        if options.type != CalculationType.MAX:
            logger.warning("Cannot perform range calculation on a single date!")
        if options.end_date not in options.summary.report_dates:
            parser.error(
                "Cannot extract key {} value for date {} "
                "not part of the simulation report dates".format(
                    options.key, options.end_date
                )
            )

    if not summary.check_sim_time(options.end_date):
        parser.error(
            "End date {} is not in the simulation time interval [{}, {}]".format(
                options.end_date, summary.start_date, summary.end_date
            )
        )


def apply_calculation(option):
    summary = option.summary
    time_range = summary.time_range(
        start=option.start_date, end=option.end_date, interval="1d"
    )
    kw_data = np.array(summary.blocked_production(option.key, time_range))
    if option.type == CalculationType.MAX:
        return np.max(kw_data)
    if option.type == CalculationType.MEAN:
        return np.mean(kw_data)
    if option.type == CalculationType.MEDIAN:
        return np.median(kw_data)
    if option.type == CalculationType.PERCENTILE:
        return np.percentile(kw_data, option.percentile)
    if option.type == CalculationType.CUMULATIVE:
        return np.sum(kw_data)


def extract_value(summary, key, date):
    return summary.get_interp(key, date=date)


def write_result(path, result, multiplier):
    with open(path, "w") as f:
        f.write("{0:.10f}\n".format((multiplier * result)))
