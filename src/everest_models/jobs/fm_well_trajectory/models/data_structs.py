from typing import Dict, NamedTuple, Optional, Tuple

import numpy
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
    deviation: Tuple[NDArray[numpy.float64], NDArray[numpy.float64]]
    inclination: NDArray[numpy.float64]
    azimuths: NDArray[numpy.float64]
    lengths: NDArray[numpy.float64]


class Trajectory(NamedTuple):
    x: NDArray[numpy.float64]
    y: NDArray[numpy.float64]
    z: NDArray[numpy.float64]


class CalculatedTrajectory(NamedTuple):
    coordinates: Trajectory
    dogleg: NDArray[numpy.float64]
    deviation: Tuple[NDArray[numpy.float64], NDArray[numpy.float64]]
    inclination: NDArray[numpy.float64]
    azimuth: NDArray[numpy.float64]
    length: NDArray[numpy.float64]
