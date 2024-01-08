from typing import Dict, Tuple

from pydantic import RootModel

from everest_models.jobs.shared.models import BaseFrozenConfig, WellConfig
from everest_models.jobs.shared.models import Well as _Well


class Well(_Well):
    drill_time: int


class Wells(WellConfig):
    root: Tuple[Well, ...]


class Optimizer(BaseFrozenConfig, RootModel):
    root: Dict[str, float]
