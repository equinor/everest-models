import logging
import pathlib
from typing import Dict, Iterable, Iterator, Optional, Tuple

import numpy
from numpy.typing import NDArray

from .dogleg import compute_dogleg_severity, try_fixing_dog_leg
from .geometry import compute_geometry
from .interpolation import interpolate_points
from .models.config import SimpleInterpolationConfig, WellConfig
from .models.data_structs import CalculatedTrajectory, Trajectory
from .outputs import write_path_files, write_resinsight, write_well_costs, write_wicalc
from .well_costs import compute_well_costs

logger = logging.getLogger(__name__)


def _check_kickoff_alignment(
    wells: Iterable[WellConfig], trajectories: Dict[str, Trajectory]
) -> None:
    if bad_alignments := ", ".join(
        well.name
        for well in wells
        if (
            trajectories[well.name].x[0] != trajectories[well.name].x[1]
            or trajectories[well.name].y[0] != trajectories[well.name].y[1]
        )
    ):
        logger.warning(
            "Kickoff missing or not directly underneath the platform.\n"
            f"\twells: {bad_alignments}"
        )


def _generate_coordinates_dogleg(
    wells: Iterable[WellConfig],
    interpolation: SimpleInterpolationConfig,
    trajectories: Dict[str, Trajectory],
) -> Iterator[Tuple[str, Trajectory, NDArray[numpy.float64]]]:
    for well in wells:
        trajectory = trajectories[well.name]
        for _ in range(interpolation.trial_number):
            if trajectory.x is not None:
                coordinates = interpolate_points(trajectory, interpolation.length)
                dogleg_severities = compute_dogleg_severity(coordinates)
            if numpy.amax(dogleg_severities) < well.dogleg:
                break
            trajectory = try_fixing_dog_leg(
                interpolation.trial_step, trajectory, coordinates, dogleg_severities
            )
        else:
            logger.warning("Maximum iteration reached, well skipped")
            continue
        yield well.name, coordinates, dogleg_severities


def _compute_well_trajectory(
    wells: Iterable[WellConfig],
    interpolation: SimpleInterpolationConfig,
    trajectories: Dict[str, Trajectory],
) -> Dict[str, CalculatedTrajectory]:
    _check_kickoff_alignment(wells, trajectories)
    return {
        well: CalculatedTrajectory(coordinates, dogleg, *compute_geometry(coordinates))
        for well, coordinates, dogleg in _generate_coordinates_dogleg(
            wells, interpolation, trajectories
        )
    }


def well_trajectory_simple(
    wells: Iterable[WellConfig],
    interpolation: SimpleInterpolationConfig,
    npv_input_file: Optional[pathlib.Path],
    guide_points: Dict[str, Trajectory],
) -> None:
    points = _compute_well_trajectory(wells, interpolation, guide_points)
    logger.info("Writing interpolation results to 'well_geometry.txt;")
    write_wicalc(
        results=points,
        path=pathlib.Path("well_geometry.txt"),
        wells={well.name: well for well in wells},
    )
    logger.info("Writing ResInsight files")
    write_resinsight(points)
    if npv_input_file is not None:
        costs = compute_well_costs(wells)
        logger.info("Writing well costs")
        write_well_costs(costs, npv_input_file)
    logger.info("Writing PATH files")
    write_path_files(
        (pathlib.Path(f"PATH_{well}").with_suffix(".txt"), trajectory)
        for well, trajectory in points.items()
    )
