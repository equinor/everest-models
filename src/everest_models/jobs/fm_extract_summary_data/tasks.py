import argparse
import datetime
import logging
import math
from collections.abc import Callable
from enum import Enum
from pathlib import Path
from typing import Any

import numpy as np
from resdata.summary import Summary

from everest_models.jobs.fm_extract_summary_data.parser import (
    _as_list,
    _parse_keyword_entry,
    _parse_section,
)

logger = logging.getLogger(__name__)


def _entry_dates(
    summary: Summary,
    entry: Any,
    start_date: datetime.date | None,
    end_date: datetime.date | None,
) -> tuple[datetime.date | None, datetime.date | None]:
    summary_dates = getattr(summary, "dates", None)
    report_dates = [date.date() for date in summary_dates] if summary_dates else []
    effective_start = entry.start_date or start_date
    effective_end = (
        entry.end_date or end_date or (report_dates[-1] if report_dates else None)
    )
    if (
        effective_start is not None
        and effective_end is not None
        and effective_start > effective_end
    ):
        raise ValueError("Entry start-date cannot be after end-date")
    for name, value in (("start-date", effective_start), ("end-date", effective_end)):
        if value is not None and report_dates and value not in report_dates:
            raise ValueError(f"Entry {name} '{value}' is not a summary report date")
    return effective_start, effective_end


_STATISTICS: dict[str, Callable[[Any], Any]] = {
    "min": np.min,
    "max": np.max,
    "mean": np.mean,
    "median": np.median,
}


def extract_vector_value(
    summary: Summary,
    key: str,
    aggregation: str | None = None,
    start_date: datetime.date | None = None,
    end_date: datetime.date | None = None,
    output_date: datetime.date | str | None = None,
) -> tuple[float, str]:
    """Extract a summary vector value by date or statistical aggregation."""
    if key not in summary:
        raise ValueError(f"Vector '{key}' not found in summary")
    if aggregation is not None and output_date is not None:
        raise ValueError("Use either aggregation or output-date, not both")

    time_index = None
    if aggregation is not None and (start_date is not None or end_date is not None):
        report_dates = [date.date() for date in summary.dates]
        time_index = summary.time_range(
            start=start_date or report_dates[0],
            end=end_date or report_dates[-1],
            interval="1d",
        )
    if time_index is None:
        raw_values = summary.numpy_vector(key)
    else:
        raw_values = summary.numpy_vector(key, time_index=time_index)
    values = [float(value) for value in raw_values]
    finite_values = [value for value in values if not math.isnan(value)]
    if not finite_values:
        raise ValueError(f"Vector '{key}' does not contain any finite values")

    if output_date is not None:
        selection = str(output_date).strip()
        dates = [
            (summary.start_time + datetime.timedelta(days=float(day))).strftime(
                "%Y-%m-%d %H:%M:%S"
            )
            for day in summary.numpy_vector("TIME")
        ]
        normalized_date = f"{selection} 00:00:00" if len(selection) == 10 else selection
        if normalized_date not in dates:
            raise ValueError(f"output-date '{selection}' not found for vector '{key}'")
        value = values[dates.index(normalized_date)]
        if math.isnan(value):
            raise ValueError(f"output-date '{selection}' for vector '{key}' is NaN")
        return value, f"date={normalized_date}"

    if aggregation is None:
        return finite_values[-1], "last"
    if aggregation not in _STATISTICS:
        raise ValueError("aggregation must be min, max, mean, or median")
    return float(_STATISTICS[aggregation](finite_values)), aggregation


def _get_fip_suffix(fip_key: str) -> str:
    keyword = fip_key.strip().upper()
    if not keyword.startswith("FIP") or len(keyword) < 6:
        raise ValueError(f"Invalid fip_key='{fip_key}'")
    return keyword[3:6]


def extract_static_targets(
    summary: Summary,
    config: dict[str, Any],
    start_date: datetime.date | None = None,
    end_date: datetime.date | None = None,
) -> dict[str, float]:
    """Extract and transform targets described by static-upload configuration."""
    targets: dict[str, float] = {}
    for index, raw_section in enumerate(_as_list(config.get("fip-section")), start=1):
        section = _parse_section(raw_section, index)
        suffix = _get_fip_suffix(section.fip_key)
        for region in section.fip_region:
            vector_name = f"{region.key.upper()}{suffix}:{region.region_number}"
            try:
                entry_start, entry_end = _entry_dates(
                    summary, region, start_date, end_date
                )
                value, _ = extract_vector_value(
                    summary,
                    vector_name,
                    start_date=entry_start,
                    end_date=entry_end,
                    aggregation=region.aggregation,
                    output_date=region.output_date,
                )
            except ValueError as error:
                logger.warning(error)
                continue
            targets[region.output] = value / region.unit_conversion

    for index, raw_entry in enumerate(_as_list(config.get("key-section")), start=1):
        entry = _parse_keyword_entry(raw_entry, index)
        try:
            entry_start, entry_end = _entry_dates(summary, entry, start_date, end_date)
            value, _ = extract_vector_value(
                summary,
                entry.key,
                start_date=entry_start,
                end_date=entry_end,
                aggregation=entry.aggregation,
                output_date=entry.output_date,
            )
        except ValueError as error:
            logger.warning(error)
            continue
        targets[entry.output] = value / entry.unit_conversion

    if not targets:
        raise ValueError("Config must contain at least one extractable section")
    return targets


def write_static_targets(targets: dict[str, float]) -> None:
    """Write extracted targets using the output paths supplied by the config."""
    for output_path, value in targets.items():
        Path(output_path).write_text(f"{value:.10f}\n", encoding="utf-8")


def extract_value(
    summary: Summary, key: str, end_date: datetime.date, **kwargs
) -> float:
    return summary.get_interp(key, date=end_date)


def _extract_statistic(
    summary: Summary,
    key: str,
    start_date: datetime.date,
    end_date: datetime.date,
    statistic: Callable[[Any], Any],
) -> float:
    values = summary.numpy_vector(
        key,
        time_index=summary.time_range(start=start_date, end=end_date, interval="1d"),
    )
    return float(statistic(values))


def _extract_diff(
    summary: Summary, key: str, start_date: datetime.date, end_date: datetime.date
) -> float:
    return summary.get_interp(key, date=end_date) - summary.get_interp(
        key, date=start_date
    )


class CalculationType(Enum):
    MAX = "max"
    MIN = "min"
    MEAN = "mean"
    MEDIAN = "median"
    DIFF = "diff"

    def __eq__(self, other):
        return self.value == other

    def extract(
        self,
        summary: Summary,
        key: str,
        start_date: datetime.date,
        end_date: datetime.date,
    ) -> float | None:
        if self == self.DIFF:
            return _extract_diff(summary, key, start_date, end_date)
        statistic = _STATISTICS[self.value]
        return _extract_statistic(summary, key, start_date, end_date, statistic)

    @classmethod
    def types(cls):
        return tuple(el.value for el in cls)


def validate_arguments(options: argparse.Namespace) -> argparse.Namespace:
    errors = []
    available_dates = [d.date() for d in options.summary.dates]
    output_date = getattr(options, "output_date", None)

    if options.end_date is None:
        options.end_date = available_dates[-1]

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
    if output_date is not None and output_date not in available_dates:
        errors.append(
            f"Output date '{output_date}' is not part of the simulation report dates"
        )
    if errors:
        raise argparse.ArgumentTypeError("\n".join(errors))
    return options
