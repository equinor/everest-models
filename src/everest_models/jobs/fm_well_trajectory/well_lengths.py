import logging
from pathlib import Path
from typing import Dict, Iterable

import pandas as pd

from .models.config import WellConfig

logger = logging.getLogger(__name__)

MDMSL = -1


def _read_well_length(well: str) -> float:
    """Read well length from a deviation file"""

    if not (path := Path(f"wellpaths/{well}").with_suffix(".dev")).exists():
        logger.warning(f"File does not exist, {path}")
        return 0.0

    return float(
        pd.read_csv(
            path,
            skiprows=2,
            skipfooter=2,
            engine="python",
            sep=r"\s+",
        ).iloc[-1, MDMSL]
    )


def compute_well_lengths(wells: Iterable[WellConfig]) -> Dict[str, float]:
    """Compute well lengths in km based on deviation files"""
    return {well.name: _read_well_length(well.name) / 1000.0 for well in wells}
