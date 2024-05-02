from typing import Dict, Tuple

from everest_models.jobs.shared.models import RootModelConfig
from everest_models.jobs.shared.models import Well as _Well
from everest_models.jobs.shared.models import Wells as _Wells


class Well(_Well):
    drill_time: int


class Wells(_Wells):
    root: Tuple[Well, ...]


class Optimizer(RootModelConfig):
    root: Dict[str, float]
