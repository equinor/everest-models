from typing import Dict, Tuple

from everest_models.jobs.shared.models import BaseFrozenConfig, WellConfig
from everest_models.jobs.shared.models import Well as _Well


class Well(_Well):
    drill_time: int


class Wells(WellConfig):
    __root__: Tuple[Well, ...]


class Optimizer(BaseFrozenConfig):
    __root__: Dict[str, float]
