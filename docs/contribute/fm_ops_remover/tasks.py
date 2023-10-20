from typing import Iterable

from everest_models.jobs.shared.models import WellConfig


def remove_operations(wells: WellConfig, well_names: Iterable[str]) -> None:
    """Set well operations to None for well's name in `well_names`.

    Args:
        wells (WellListModel): wells collected from user defined wells.json
        well_names (Iterable[str]): a collection of well names to be matched
    """
    for well in wells:
        if well.name in well_names:
            well.ops = None
