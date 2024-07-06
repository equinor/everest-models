import itertools
import logging
from pathlib import Path
from typing import Any, Dict, Final, Iterable, NamedTuple, Optional, Tuple

import numpy as np

from ..shared.io_utils import load_json
from .models.config import PlatformConfig, ReferencesConfig, ScalesConfig, WellConfig
from .models.data_structs import Trajectory

logger = logging.getLogger("well_trajectory")

P1: Final = tuple(f"p1_{tag}" for tag in ("x", "y", "z"))
P2: Final = tuple(f"p2_{tag}" for tag in ("a", "b", "c"))
P3: Final = tuple(f"p3_{tag}" for tag in ("x", "y", "z"))
PLATFORMS: Final = tuple(f"platform_{tag}" for tag in ("x", "y", "k"))
M1: Final = "mlt_p1_z"
M2: Final = tuple(f"mlt_p2_{tag}" for tag in ("a", "b", "c"))
M3: Final = tuple(f"mlt_p3_{tag}" for tag in ("x", "y", "z"))


class _Point(NamedTuple):
    x: float
    y: float
    z: float


def _rescale(point: float, scale: float, reference: float):
    return scale * point + reference


def _read_files(*args: str) -> Dict[str, Any]:
    return {
        filename: (load_json(Path(filename).with_suffix(".json")))
        for filename in args
        if Path(filename).with_suffix(".json").exists()
    }


def _read_platform_and_kickoff(
    input_files: Dict[str, Any],
    scales: ScalesConfig,
    references: ReferencesConfig,
    platform_config: PlatformConfig,
) -> Tuple[_Point, Optional[float]]:
    def _get_from_platform_file(platform_file: str, attr: str) -> Optional[float]:
        value = input_files.get(platform_file, {}).get(platform_config.name)
        if value is not None:
            logger.warning(
                f"File: {platform_file}.json found, overriding '{attr}' "
                f"for '{platform_config.name}' in configuration."
            )
            scale = getattr(scales, attr)
            ref = getattr(references, attr)
            if scale is None or ref is None:
                raise ValueError(
                    f"Either 'references.{attr}' or 'scales.{attr}' missing in configuration"
                )
            value = _rescale(value, scale, ref)
        else:
            # If necessary, get the value from the platform configuration:
            value = getattr(platform_config, attr)

        return value

    px = _get_from_platform_file("platform_x", "x")
    py = _get_from_platform_file("platform_y", "y")
    pk = _get_from_platform_file("platform_k", "k")

    # px and py are mandatory, pk may be `None`:
    assert px is not None
    assert py is not None

    return _Point(x=px, y=py, z=0.0), pk


def _get_rescaled_point(
    point_files: Iterable[str],
    input_files: Dict[str, Any],
    well_name: str,
    scales: ScalesConfig,
    references: ReferencesConfig,
) -> _Point:
    px, py, pz = (input_files[item][well_name] for item in point_files)
    return _Point(
        x=_rescale(px, scales.x, references.x),
        y=_rescale(py, scales.y, references.y),
        z=_rescale(pz, scales.z, references.z),
    )


def _construct_midpoint(
    a: float, b: float, c: float, p1: _Point, p3: _Point
) -> Tuple[float, float, float]:
    return _Point(
        x=b * (p3.y - p1.y) + a * (p3.x - p1.x) + p1.x,
        y=b * (p1.x - p3.x) + a * (p3.y - p1.y) + p1.y,
        z=p3.z + c * (p1.z - p3.z),
    )


def _read_trajectory(
    scales: ScalesConfig,
    references: ReferencesConfig,
    well_name: str,
    platform_config: Optional[PlatformConfig],
    point_files: Dict[str, Any],
    platform_files: Dict[str, Any],
) -> Trajectory:
    p1 = _get_rescaled_point(P1, point_files, well_name, scales, references)
    p3 = _get_rescaled_point(P3, point_files, well_name, scales, references)
    a, b, c = [point_files[key][well_name] for key in P2]
    p2 = _construct_midpoint(a, b, c, p1, p3)

    if platform_config is None:
        # Add a platform right above the first guide point:
        x, y, z = [p1.x], [p1.y], [p1.z]
    else:
        platform_point, platform_k = _read_platform_and_kickoff(
            platform_files, scales, references, platform_config
        )
        # The platform must be at z=0:
        x, y, z = [platform_point.x], [platform_point.y], [0.0]
        if platform_k is not None:
            # Add the kickoff right below the platform:
            x.append(platform_point.x)
            y.append(platform_point.y)
            z.append(platform_k)

    return Trajectory(
        x=np.array(x + [p1.x, p2.x, p3.x]),
        y=np.array(y + [p1.y, p2.y, p3.y]),
        z=np.array(z + [p1.z, p2.z, p3.z]),
    )


def read_trajectories(
    scales: ScalesConfig,
    references: ReferencesConfig,
    wells: Iterable[WellConfig],
    platforms: Iterable[PlatformConfig],
) -> Dict[str, Trajectory]:
    point_files = _read_files(*P1, *P2, *P3)
    missing_files = [
        point_file
        for point_file in itertools.chain(P1, P2, P3)
        if point_file not in point_files
    ]
    if missing_files:
        raise ValueError(f"Missing point files: {missing_files}")
    if missing_files:
        raise ValueError(f"Missing point files: {missing_files}")
    missing_wells = [
        f"{point_file}/{well.name}"
        for point_file in itertools.chain(P1, P2, P3)
        for well in wells
        if well.name not in point_files[point_file]
    ]
    if missing_wells:
        raise ValueError(f"Missing wells: {missing_wells}")

    platform_files = _read_files(*PLATFORMS)

    return {
        well.name: _read_trajectory(
            scales=scales,
            references=references,
            well_name=well.name,
            platform_config=next(
                (item for item in platforms if item.name == well.platform), None
            ),
            point_files=point_files,
            platform_files=platform_files,
        )
        for well in wells
    }


def _read_lateral_files(wells: Iterable[WellConfig]) -> Dict[str, Any]:
    lateral_files = _read_files(M1, *M2, *M3)
    if M1 not in lateral_files:
        return {}

    lateral_names = list(lateral_files[M1].keys())

    # All branches must have a parent well:
    orphans = set(lateral_names) - {well.name for well in wells}
    if orphans:
        raise ValueError(f"Found branches without parent well: {list(orphans)}")

    # Check if all branches are correctly specified.
    missing = [
        filename
        for filename in itertools.chain(M2, M3)
        if filename not in lateral_files
    ]
    if missing:
        msg = f"Missing coordinate files: '{missing}'"
        raise ValueError(msg)
    missing = [
        f"{filename}/{name}"
        for name in lateral_names
        for filename in itertools.chain(M2, M3)
        if name not in lateral_files[filename]
    ]
    if missing:
        msg = f"Missing wells in coordinate files: {missing}"
        raise ValueError(msg)
    missing = [
        f"{filename}/{name}/{index}"
        for name in lateral_names
        for index in lateral_files[M1][name]
        for filename in itertools.chain(M2, M3)
        if index not in lateral_files[filename][name]
    ]
    if missing:
        msg = f"Missing branches in coordinate files: {missing}"
        raise ValueError(msg)
    return lateral_files


def _find_mlt_p1(
    scales: ScalesConfig,
    references: ReferencesConfig,
    well_name: str,
    branch: str,
    lateral_files: Dict[str, Any],
) -> Tuple[float, _Point]:
    # Get the true depth:
    z = _rescale(lateral_files[M1][well_name][branch], scales.z, references.z)

    # Read the trajectory of the well, which must be available:
    dev = np.genfromtxt(
        f"wellpaths/{well_name}.dev",
        dtype=np.float64,
        skip_header=1,
        skip_footer=1,
        names=True,
    )

    # Check the depth we want:
    if z < dev["TVDMSL"][0] or z > dev["TVDMSL"][-1]:
        msg = f"Branch '{branch}' does not start on well '{well_name}'"
        raise ValueError(msg)

    # Return the measured depth and the coordinates of the start of the branch:
    idx = np.argmin(abs(dev["TVDMSL"] - z))
    return (
        dev["MDMSL"][idx],
        _Point(x=dev["X"][idx], y=dev["Y"][idx], z=dev["TVDMSL"][idx]),
    )


def _read_lateral(
    scales: ScalesConfig,
    references: ReferencesConfig,
    well_name: str,
    branch: str,
    lateral_files: Dict[str, Any],
) -> Tuple[float, Trajectory]:
    # Find the first point of the branch:
    md, mlt_p1 = _find_mlt_p1(scales, references, well_name, branch, lateral_files)

    # Find the end-point of the branch:
    mlt_p3 = _Point(
        x=_rescale(lateral_files[M3[0]][well_name][branch], scales.x, references.x),
        y=_rescale(lateral_files[M3[1]][well_name][branch], scales.y, references.y),
        z=_rescale(lateral_files[M3[2]][well_name][branch], scales.z, references.z),
    )

    # Find the midpoint between the beginning and end of the branch:
    a, b, c = [lateral_files[key][well_name][branch] for key in M2]
    mlt_p2 = _construct_midpoint(a, b, c, mlt_p1, mlt_p3)

    return md, Trajectory(
        x=np.array([mlt_p1.x, mlt_p2.x, mlt_p3.x]),
        y=np.array([mlt_p1.y, mlt_p2.y, mlt_p3.y]),
        z=np.array([mlt_p1.z, mlt_p2.z, mlt_p3.z]),
    )


def read_laterals(
    scales: ScalesConfig,
    references: ReferencesConfig,
    wells: Iterable[WellConfig],
) -> Dict[str, Dict[str, Tuple[float, Trajectory]]]:
    lateral_files = _read_lateral_files(wells)
    return (
        {
            well: {
                branch: _read_lateral(scales, references, well, branch, lateral_files)
                for branch in lateral_files[M1][well]
            }
            for well in lateral_files[M1]
        }
        if M1 in lateral_files
        else {}
    )
