import math

import numpy
from numpy.typing import NDArray

from spinningjenny.jobs.fm_well_trajectory.models.data_structs import (
    Geometry,
    Trajectory,
)


def compute_deviations(x: NDArray[numpy.float64]) -> NDArray[numpy.float64]:
    deviations = numpy.empty(len(x), dtype=numpy.float64)
    deviations[0] = 0.0
    deviations[1:] = x[1:] - x[0]
    return deviations


def _get_diff_array(trajectory: Trajectory) -> NDArray[numpy.float64]:
    return numpy.array(
        [
            trajectory.x[1:] - trajectory.x[:-1],
            trajectory.y[1:] - trajectory.y[:-1],
            trajectory.z[1:] - trajectory.z[:-1],
        ]
    )


def compute_inclinations(
    trajectory: Trajectory,
) -> NDArray[numpy.float64]:
    diffs = _get_diff_array(trajectory)
    vec_z = numpy.array([0, 0, 1])
    inclinations = numpy.empty(len(trajectory.x), dtype=numpy.float64)
    inclinations[:-1] = numpy.arctan2(
        numpy.linalg.norm(numpy.cross(diffs, vec_z, axis=0), axis=0),
        numpy.dot(vec_z, diffs),
    )
    inclinations[-1] = inclinations[-2]
    return inclinations


def compute_azimuths(
    trajectory: Trajectory,
    eps: float = 1e-5,
) -> NDArray[numpy.float64]:
    azimuths = numpy.zeros(len(trajectory.x), dtype=numpy.float64)
    diffs = _get_diff_array(trajectory)
    abs_diffs = numpy.abs(diffs)
    azimuths[:-1] = numpy.where(
        (abs_diffs[0] > eps) & (abs_diffs[1] > eps),
        numpy.arctan2(numpy.dot([1, 0, 0], diffs), numpy.dot([0, 1, 0], diffs)),
        0.0,
    )
    azimuths[:-1] = numpy.where(
        (abs_diffs[0] < eps) & (abs_diffs[1] >= eps) & (diffs[1] <= 0),
        math.pi,
        azimuths[:-1],
    )
    azimuths[:-1] = numpy.where(
        (abs_diffs[0] >= eps) & (abs_diffs[1] < eps) & (diffs[0] > 0),
        math.pi / 2,
        azimuths[:-1],
    )
    azimuths[:-1] = numpy.where(
        (abs_diffs[0] >= eps) & (abs_diffs[1] < eps) & (diffs[0] <= 0),
        3 * math.pi / 2,
        azimuths[:-1],
    )
    azimuths[-1] = azimuths[-2]
    return azimuths


def compute_interval_lengths(trajectory: Trajectory) -> NDArray[numpy.float64]:
    return numpy.sqrt(
        (trajectory.x[1:] - trajectory.x[:-1]) ** 2
        + (trajectory.y[1:] - trajectory.y[:-1]) ** 2
        + (trajectory.z[1:] - trajectory.z[:-1]) ** 2
    )


def compute_geometry(trajectory: Trajectory) -> Geometry:
    return Geometry(
        deviation=(compute_deviations(trajectory.x), compute_deviations(trajectory.y)),
        inclination=compute_inclinations(trajectory),
        azimuths=compute_azimuths(trajectory),
        lengths=numpy.cumsum(
            numpy.append(0.0, numpy.array(compute_interval_lengths(trajectory)))
        ),
    )
