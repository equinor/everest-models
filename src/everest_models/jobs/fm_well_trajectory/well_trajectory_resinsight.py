import itertools
import logging
import signal
import sys
from pathlib import Path
from typing import Dict, Optional

import rips

from .models.config import ConfigSchema
from .outputs import write_well_costs
from .read_trajectories import read_laterals
from .resinsight import (
    create_branches,
    create_well,
    create_well_logs,
    make_perforations,
    read_wells,
)
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
        instance = rips.Instance.launch(self._executable, console=True, launch_port=0)
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


def _save_project(project_path: str, project: rips.Project):
    project_file = str(project_path / ".model.rsp")
    logger.info(f"Saving project to: {project_file}")
    project.save(project_file)


def _save_paths(project_path: str, project: rips.Project, mds: float):
    _save_project(project_path, project)
    logger.info(
        f"Calling 'export_well_paths' on the resinsight project\ncwd = {Path.cwd()}"
    )
    project.export_well_paths(well_paths=None, md_step_size=mds)


def well_trajectory_resinsight(
    config: ConfigSchema,
    eclipse_model: Path,
    guide_points: Dict[str, Trajectory],
    project_path: Optional[Path] = None,
) -> None:
    mlt_guide_points = {}
    if project_path is None:
        project_path = Path.cwd()
    with ResInsight(
        "" if config.resinsight_binary is None else str(config.resinsight_binary)
    ) as resinsight:
        resinsight.project.load_case(str(eclipse_model.with_suffix(".EGRID")))

        if config.interpolation.type == "resinsight":
            # Interpolate trajectories, keep the created well paths inc case we
            # will turn them into multi-lateral trajectories below:
            well_paths = {
                well_config.name: create_well(
                    config.connections,
                    well_config,
                    guide_points[well_config.name],
                    resinsight.project,
                )
                for well_config in config.wells
            }
            _save_paths(
                project_path,
                resinsight.project,
                config.interpolation.measured_depth_step,
            )

            mlt_guide_points = read_laterals(
                config.scales, config.references, config.wells
            )
            if mlt_guide_points:
                # Create multi-lateral trajectories based on the trajectories we
                # made before:
                for well_config in config.wells:
                    if well_config.name in mlt_guide_points:
                        create_branches(
                            well_config,
                            well_paths[well_config.name],
                            mlt_guide_points[well_config.name],
                            resinsight.project,
                        )
                _save_paths(
                    project_path,
                    resinsight.project,
                    config.interpolation.measured_depth_step,
                )
        else:
            # Simple interpolation, use saved trajectories:
            read_wells(
                resinsight.project,
                project_path / "wellpaths",
                [well.name for well in config.wells],
                config.connections,
            )
        create_well_logs(
            config.connections.perforations,
            resinsight.project,
            eclipse_model,
            project_path,
            config.connections.date,
        )
        wells = itertools.filterfalse(
            lambda x: x is None,
            (
                make_perforations(
                    resinsight.project,
                    well_path.name,
                    config.connections.perforations,
                    config.wells,
                    project_path,
                )
                for well_path in resinsight.project.well_paths()
            ),
        )
        if config.npv_input_file is not None:
            write_well_costs(
                costs=compute_well_costs(wells),
                npv_file=config.npv_input_file,
            )
        else:
            all(wells)  # consume generator without collecting yields

        _save_project(project_path, resinsight.project)

    return mlt_guide_points
