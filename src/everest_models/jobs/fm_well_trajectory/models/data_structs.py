from typing import Dict, NamedTuple, Optional, Tuple

import numpy as np
from numpy.typing import NDArray


class Domain(NamedTuple):
    min: float
    max: float


class Perforation(NamedTuple):
    dynamic: Dict[str, Domain]
    static: Dict[str, Domain]
    formations: Tuple[int, ...]


class Platform(NamedTuple):
    x: float
    y: float
    z: float
    k: float


class Well(NamedTuple):
    group: str
    phase: str
    skin: float
    radius: float
    dogleg: float
    cost: float
    platform: Optional[str] = None


class Geometry(NamedTuple):
    deviation: Tuple[NDArray[np.float64], NDArray[np.float64]]
    inclination: NDArray[np.float64]
    azimuths: NDArray[np.float64]
    lengths: NDArray[np.float64]


class Trajectory(NamedTuple):
    x: NDArray[np.float64]
    y: NDArray[np.float64]
    z: NDArray[np.float64]


class CalculatedTrajectory(NamedTuple):
    coordinates: Trajectory
    dogleg: NDArray[np.float64]
    deviation: Tuple[NDArray[np.float64], NDArray[np.float64]]
    inclination: NDArray[np.float64]
    azimuth: NDArray[np.float64]
    length: NDArray[np.float64]
