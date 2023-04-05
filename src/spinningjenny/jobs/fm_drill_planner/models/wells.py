from typing import Dict, Tuple

from spinningjenny.jobs.shared.models import BaseFrozenConfig, WellListModel, WellModel


class Well(WellModel):
    drill_time: int


class Wells(WellListModel):
    __root__: Tuple[Well, ...]


class Optimizer(BaseFrozenConfig):
    __root__: Dict[str, float]
