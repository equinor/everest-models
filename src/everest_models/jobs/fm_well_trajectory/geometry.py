import math

import numpy as np
from numpy.typing import NDArray

from everest_models.jobs.fm_well_trajectory.models.data_structs import (
    Geometry,
    Trajectory,
)


def compute_deviations(x: NDArray[np.float64]) -> NDArray[np.float64]:
    deviations = np.empty(len(x), dtype=np.float64)
    deviations[0] = 0.0
    deviations[1:] = x[1:] - x[0]
    return deviations


def _get_diff_array(trajectory: Trajectory) -> NDArray[np.float64]:
    return np.array(
        [
            trajectory.x[1:] - trajectory.x[:-1],
            trajectory.y[1:] - trajectory.y[:-1],
            trajectory.z[1:] - trajectory.z[:-1],
        ]
    )


def compute_inclinations(
    trajectory: Trajectory,
) -> NDArray[np.float64]:
    diffs = _get_diff_array(trajectory)
    vec_z = np.array([0, 0, 1])
    inclinations = np.empty(len(trajectory.x), dtype=np.float64)
    inclinations[:-1] = np.arctan2(
        np.linalg.norm(np.cross(diffs, vec_z, axis=0), axis=0),
        np.dot(vec_z, diffs),
    )
    inclinations[-1] = inclinations[-2]
    return inclinations


def compute_azimuths(
    trajectory: Trajectory,
    eps: float = 1e-5,
) -> NDArray[np.float64]:
    azimuths = np.zeros(len(trajectory.x), dtype=np.float64)
    diffs = _get_diff_array(trajectory)
    abs_diffs = np.abs(diffs)
    azimuths[:-1] = np.where(
        (abs_diffs[0] > eps) & (abs_diffs[1] > eps),
        np.arctan2(np.dot([1, 0, 0], diffs), np.dot([0, 1, 0], diffs)),
        0.0,
    )
    azimuths[:-1] = np.where(
        (abs_diffs[0] < eps) & (abs_diffs[1] >= eps) & (diffs[1] <= 0),
        math.pi,
        azimuths[:-1],
    )
    azimuths[:-1] = np.where(
        (abs_diffs[0] >= eps) & (abs_diffs[1] < eps) & (diffs[0] > 0),
        math.pi / 2,
        azimuths[:-1],
    )
    azimuths[:-1] = np.where(
        (abs_diffs[0] >= eps) & (abs_diffs[1] < eps) & (diffs[0] <= 0),
        3 * math.pi / 2,
        azimuths[:-1],
    )
    azimuths[-1] = azimuths[-2]
    return azimuths


def compute_interval_lengths(trajectory: Trajectory) -> NDArray[np.float64]:
    return np.sqrt(
        (trajectory.x[1:] - trajectory.x[:-1]) ** 2
        + (trajectory.y[1:] - trajectory.y[:-1]) ** 2
        + (trajectory.z[1:] - trajectory.z[:-1]) ** 2
    )


def compute_geometry(trajectory: Trajectory) -> Geometry:
    return Geometry(
        deviation=(compute_deviations(trajectory.x), compute_deviations(trajectory.y)),
        inclination=compute_inclinations(trajectory),
        azimuths=compute_azimuths(trajectory),
        lengths=np.cumsum(
            np.append(0.0, np.array(compute_interval_lengths(trajectory)))
        ),
    )
