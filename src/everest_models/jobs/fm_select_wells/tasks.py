import argparse
import datetime
import logging

from everest_models.jobs.shared.models import Wells

logger = logging.getLogger(__name__)


def get_well_number(options: argparse.Namespace) -> int | None:
    """Collect well number from job session context

    Args:
        options (argparse.Namespace): job session context

    Returns:
        Optional[int]: well number
    """
    if hasattr(options, "file_path"):
        if options.lint:
            return options.file_path
        return round(options.file_path)
    if hasattr(options, "well_number"):
        return options.well_number if options.lint else round(options.well_number)
    return None


def select_wells(
    wells: Wells,
    max_date: datetime.date | None,
    number_of_wells: int | None,
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

    if number_of_wells is not None and number_of_wells < len(wells.root):
        wells.root = tuple(
            sorted(wells.root, key=lambda k: k.readydate)[:number_of_wells]
        )
