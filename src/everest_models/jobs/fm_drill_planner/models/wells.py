from typing import Dict, Tuple

from everest_models.jobs.shared.models import BaseFrozenConfig
from everest_models.jobs.shared.models import Well as _Well
from everest_models.jobs.shared.models import WellConfig


class Well(_Well):
    drill_time: int


class Wells(WellConfig):
    __root__: Tuple[Well, ...]


class Optimizer(BaseFrozenConfig):
    __root__: Dict[str, float]
