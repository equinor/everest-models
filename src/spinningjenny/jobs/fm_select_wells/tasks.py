import argparse
import datetime
import logging
from typing import Callable, Optional, Tuple

from spinningjenny.jobs.shared.converters import rescale_value
from spinningjenny.jobs.shared.models import WellListModel

logger = logging.getLogger(__name__)


def _check_bounds(
    options: argparse.Namespace, error_msgr: Callable[[str], None]
) -> None:
    errors = []

    def check(bounds, name):
        if bounds[1] < bounds[0]:
            errors.append(f"Invalid {name}: lower bound greater than upper, {bounds}")

    check(options.real_bounds, "real_bounds")
    check(options.scaled_bounds, "scaled_bounds")
    if errors:
        error_msgr("\n".join(errors))


def _equidistant_range(
    scaled_well_number: float,
    scaled_bounds: Tuple[float, float],
    real_bounds: Tuple[int, int],
) -> int:
    return max(
        real_bounds[0],
        min(
            round(
                rescale_value(
                    scaled_well_number,
                    scaled_bounds[0],
                    scaled_bounds[1],
                    float(real_bounds[0]) - 0.5,
                    float(real_bounds[1]) + 0.5,
                ),
            ),
            real_bounds[1],
        ),
    )


def get_well_number(
    options: argparse.Namespace, error_msgr: Callable[[str], None]
) -> Optional[int]:
    if hasattr(options, "file_path"):
        _check_bounds(options, error_msgr)
        if options.lint:
            return options.file_path
        return _equidistant_range(
            options.file_path, options.scaled_bounds, options.real_bounds
        )
    if hasattr(options, "well_number"):
        if options.lint:
            return options.well_number
        return round(options.well_number)
    return None


def select_wells(
    wells: WellListModel,
    max_date: datetime.date,
    number_of_wells: int,
) -> None:
    if max_date is not None:
        wells.set_wells(well for well in wells if well.readydate <= max_date)

    if not number_of_wells or len(wells) < number_of_wells:
        return

    wells.set_wells(sorted(wells, key=lambda k: k.readydate)[:number_of_wells])
