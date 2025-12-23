import logging
import math
from typing import Optional

import numpy as np
from numpy.typing import NDArray

from everest_models.jobs.fm_well_trajectory.models.data_structs import Trajectory

from .geometry import compute_azimuths, compute_inclinations, compute_interval_lengths

logger = logging.getLogger(__name__)


def _identify_most_violating_point(
    trajectory: Trajectory,
    s_trajectory: Trajectory,  # Need better name
    dogleg_severities: NDArray[np.float64],
) -> int:
    max_dls_idx = np.argmax(dogleg_severities)
    max_coors = np.array(
        [
            [
                s_trajectory.x[max_dls_idx],
                s_trajectory.y[max_dls_idx],
                s_trajectory.z[max_dls_idx],
            ]
        ]
    ).T
    dist = np.linalg.norm(
        np.array([trajectory.x[1:], trajectory.y[1:], trajectory.z[1:]]) - max_coors,
        axis=0,
    )
    return np.argmin(dist) + 1


def _move_point_towards_neighbor(
    trajectory: Trajectory,
    idx: int,
    step: float,
) -> Trajectory:
    def _calculate(value: np.float64, other: np.float64) -> np.float64:
        return value + step * (other - value)

    x, y, z = trajectory
    if idx > 1:
        x[idx], y[idx], z[idx] = (
            [
                _calculate(
                    values[idx],
                    values[idx - 1]
                    if abs(values[idx] - values[idx - 1])
                    > abs(values[idx] - values[idx + 1])
                    else values[idx + 1],
                )
                for values in trajectory
            ]
            if idx < len(x)
            else [_calculate(values[idx], values[idx - 1]) for values in trajectory]
        )

    elif abs(z[idx] - z[idx - 1]) > abs(z[idx] - z[idx + 1]):
        z[idx] = _calculate(z[idx], z[idx - 1])
    else:
        z[idx] = _calculate(z[idx], z[idx + 1])

    return Trajectory(x, y, z)


def _compute_dogleg_severities(
    dogleg_angles: NDArray[np.float64], interval_lengths: NDArray[np.float64]
) -> NDArray[np.float64]:
    severities = np.empty(len(dogleg_angles), dtype=np.float64)
    severities[0] = 0.0
    severities[1:] = (
        30.48
        * (dogleg_angles[1:] * 180 / math.pi)
        / interval_lengths[: len(dogleg_angles) - 1]
    )
    return severities


def _compute_dogleg_angles(
    inclanations: NDArray[np.float64], azimuths: NDArray[np.float64]
):
    angles = np.empty(len(inclanations), dtype=np.float64)
    angles[0] = 0.0
    angles[1:] = 2 * np.arcsin(
        np.sqrt(
            np.sin((inclanations[1:] - inclanations[:-1]) / 2) ** 2
            + np.sin(inclanations[:-1])
            * np.sin(inclanations[1:])
            * (np.sin((azimuths[1:] - azimuths[:-1]) / 2) ** 2)
        )
    )
    return angles


def compute_dogleg_severity(trajectory: Trajectory) -> NDArray[np.float64]:
    inclinations = compute_inclinations(trajectory)
    azimuths = compute_azimuths(trajectory)
    return _compute_dogleg_severities(
        _compute_dogleg_angles(inclinations, azimuths),
        compute_interval_lengths(trajectory),
    )


def try_fixing_dog_leg(
    step: float,
    trajectory: Trajectory,
    s_trajectory: Optional[Trajectory],
    dogleg_severities: NDArray[np.float64],
) -> Trajectory:
    idx = _identify_most_violating_point(trajectory, s_trajectory, dogleg_severities)
    try:
        return _move_point_towards_neighbor(trajectory, idx, step)
    except IndexError as e:
        logger.warning(e)
        return Trajectory(None, None, None)
