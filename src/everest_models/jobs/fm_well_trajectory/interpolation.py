import numpy
from scipy import interpolate

from everest_models.jobs.fm_well_trajectory.models.data_structs import Trajectory


def interpolate_points(
    trajectory: Trajectory,
    n: int,
) -> Trajectory:
    x, y, z = trajectory
    diffs = numpy.array([x[1:] - x[:-1], y[1:] - y[:-1], z[1:] - z[:-1]])
    s = numpy.zeros(len(x), dtype=float)
    s[1:] = numpy.linalg.norm(diffs, axis=0)
    s = numpy.cumsum(s)

    # Enforce the presence of the kickoff:
    xvec = numpy.append(numpy.linspace(s[0], s[0], 1), numpy.linspace(s[1], s[-1], n))
    return Trajectory(
        x=interpolate.PchipInterpolator(s, x)(xvec),
        y=interpolate.PchipInterpolator(s, y)(xvec),
        z=interpolate.PchipInterpolator(s, z)(xvec),
    )
