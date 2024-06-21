import itertools
import logging
import signal
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Dict

import rips

from .models.config import ConfigSchema, ResInsightInterpolationConfig
from .outputs import write_well_costs, write_well_geometry
from .resinsight import create_well, create_well_logs, make_perforations, read_wells
from .well_costs import compute_well_costs
from .well_trajectory_simple import Trajectory

logger = logging.getLogger(__name__)


class ResInsight:
    def __init__(self, executable: str = "") -> None:
        self._executable = executable
        signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))
        signal.signal(signal.SIGINT, lambda *_: sys.exit(0))

    def __enter__(self) -> rips.Instance:
        logger.info("Launching ResInsight...")
        instance = rips.Instance.launch(self._executable, console=True)
        if instance is None:
            msg = (
                "Failed to launch ResInsight: no executable found"
                if self._executable == ""
                else f"Failed to launch ResInsight executable: {self._executable}"
            )
            raise ConnectionError(msg)

        self._instance = instance
        return instance

    def __exit__(self, *_) -> None:
        self._instance.exit()


@contextmanager
def resinsight_project(project: rips.Project, egrid_path: str, project_file: str):
    project.load_case(egrid_path)
    yield project
    logger.info(f"Saving project to: {project_file}")
    project.save(project_file)


def well_trajectory_resinsight(
    config: ConfigSchema,
    eclipse_model: Path,
    guide_points: Dict[str, Trajectory],
    project_path: Path = Path.cwd(),
) -> None:
    with ResInsight(
        "" if config.resinsight_binary is None else str(config.resinsight_binary)
    ) as resinsight:
        with resinsight_project(
            resinsight.project,
            str(eclipse_model.with_suffix(".EGRID")),
            str(project_path / "model.rsp"),
        ) as project:
            if isinstance(config.interpolation, ResInsightInterpolationConfig):
                # Interpolate trajectories and save smooth trajectories:
                for well in config.wells:
                    project = create_well(
                        config.connections,
                        config.platforms,
                        config.interpolation.measured_depth_step,
                        well,
                        guide_points[well.name],
                        project,
                        project_path,
                    )

                write_well_geometry(config)
            else:
                # Simple interpolation, use saved trajectories:
                project = read_wells(
                    project,
                    project_path / "wellpaths",
                    [well.name for well in config.wells],
                    config.connections,
                )
            project = create_well_logs(
                config.connections.perforations,
                project,
                eclipse_model,
                project_path,
                config.connections.date,
            )
            wells = itertools.filterfalse(
                lambda x: x is None,
                (
                    make_perforations(
                        project,
                        well_path.name,
                        config.connections.perforations,
                        config.wells,
                        project_path,
                    )
                    for well_path in project.well_paths()
                ),
            )
            if config.outputs.npv_input is not None:
                write_well_costs(
                    costs=compute_well_costs(wells),
                    npv_file=config.outputs.npv_input,
                )
            else:
                all(wells)  # consume generator without collecting yields
