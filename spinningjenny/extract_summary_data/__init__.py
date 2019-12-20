from enum import Enum
import numpy as np

from spinningjenny import customized_logger

logger = customized_logger.get_logger(__name__)


class CalculationType(Enum):
    MAX = "max"
    DIFF = "diff"

    def __eq__(self, other):
        return self.value == other

    @staticmethod
    def types():
        return [el.value.lower() for el in CalculationType]


def validate_arguments(options, parser):
    summary = options.summary
    if options.key not in summary:
        parser.error("Missing required data {} in summary file.".format(options.key))

    if options.start_date:
        if options.start_date > options.end_date:
            parser.error("Start date is after end date.")

        if options.start_date not in options.summary.report_dates:
            parser.error(
                "Date {} is not part of the simulation report dates".format(
                    options.start_date
                )
            )
    if options.end_date not in options.summary.report_dates:
        parser.error(
            "Date {} is not part of the simulation report dates".format(
                options.end_date
            )
        )

    if options.start_date is None:
        logger.info(
            "Extracting key {} for single date {}".format(
                options.key, options.end_date
            )
        )


def apply_calculation(summary, calc_type, key, start_date, end_date):
    time_range = summary.time_range(start=start_date, end=end_date, interval="1d")
    kw_data = summary.numpy_vector(key, time_range)
    if calc_type == CalculationType.MAX:
        return np.max(kw_data)
    if calc_type == CalculationType.DIFF:
        star_val = summary.get_interp(key, date=start_date)
        end_val = summary.get_interp(key, date=end_date)
        return end_val - star_val


def extract_value(summary, key, date):
    return summary.get_interp(key, date=date)


def write_result(path, result, multiplier):
    with open(path, "w") as f:
        f.write("{0:.10f}\n".format((multiplier * result)))
