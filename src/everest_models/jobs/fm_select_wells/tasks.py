import argparse
import datetime
import logging
from typing import Callable, Optional, Tuple

from everest_models.jobs.shared.converters import rescale_value
from everest_models.jobs.shared.models import Wells

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
    """Collect well number from job session context

    Args:
        options (argparse.Namespace): job session context
        error_msgr (Callable[[str], None]): standard output/error writer

    Returns:
        Optional[int]: well number
    """
    if hasattr(options, "file_path"):
        _check_bounds(options, error_msgr)
        if options.lint:
            return options.file_path
        return _equidistant_range(
            options.file_path, options.scaled_bounds, options.real_bounds
        )
    if hasattr(options, "well_number"):
        return options.well_number if options.lint else round(options.well_number)
    return None


def select_wells(
    wells: Wells,
    max_date: Optional[datetime.date],
    number_of_wells: Optional[int],
) -> None:
    """Select wells.

    - Wells will first be filter by the max_date
    - If number of wells is smaller than the size of the wells,
      then reduce wells by the number of wells

    Args:
        wells (WellListModel):
        max_date (datetime.date): max allowed time for ready date
        number_of_wells (int): number of wells to be selected
    """
    if max_date:
        wells.root = tuple(well for well in wells.root if well.readydate <= max_date)

    if number_of_wells and number_of_wells < len(wells.root):
        wells.root = tuple(
            sorted(wells.root, key=lambda k: k.readydate)[:number_of_wells]
        )
