import logging
import pathlib
from typing import Dict, Iterable

import pandas

from .models.config import WellConfig

logger = logging.getLogger(__name__)

MDMSL = -1


def _read_well_length(well: str) -> float:
    """Read well length from a deviation file"""

    if not (path := pathlib.Path(f"wellpaths/{well}").with_suffix(".dev")).exists():
        logger.warning(f"File does not exist, {path}")
        return 0.0

    return float(
        pandas.read_csv(
            path,
            skiprows=2,
            skipfooter=2,
            engine="python",
            delim_whitespace=True,
        ).iloc[-1][MDMSL]
    )


def compute_well_costs(wells: Iterable[WellConfig]) -> Dict[str, float]:
    """Update well costs based on well length"""

    return {
        well.name: _read_well_length(well.name) * (well.cost / 1000.0) for well in wells
    }
