from everest_models.jobs.shared.models import RootModelConfig
from everest_models.jobs.shared.models import Well as _Well
from everest_models.jobs.shared.models import Wells as _Wells


class Well(_Well):
    drill_time: int


class Wells(_Wells):
    root: tuple[Well, ...]


class Optimizer(RootModelConfig):
    root: dict[str, float]
