import itertools
import logging
from pathlib import Path
from typing import Any, Dict, Final, Iterable, NamedTuple, Optional, Tuple

import numpy as np

from ..shared.io_utils import load_json
from .models.config import PlatformConfig, WellConfig
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


def _read_files(*args: str) -> Dict[str, Any]:
    return {
        filename: (load_json(Path(filename).with_suffix(".json")))
        for filename in args
        if Path(filename).with_suffix(".json").exists()
    }


def _get_point_for_well(
    point_files: Iterable[str],
    input_files: Dict[str, Any],
    well_name: str,
) -> _Point:
    px, py, pz = (input_files[item][well_name] for item in point_files)
    return _Point(
        x=px,
        y=py,
        z=pz,
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
    well: WellConfig,
    platform_config: Optional[PlatformConfig],
    point_files: Dict[str, Any],
    optimized_platform_loc: Dict[str, Dict[str, Optional[float]]],
) -> Trajectory:
    p1 = _get_point_for_well(P1, point_files, well.name)
    p3 = _get_point_for_well(P3, point_files, well.name)
    a, b, c = [point_files[key][well.name] for key in P2]
    p2 = _construct_midpoint(a, b, c, p1, p3)

    # Check for each platform attribute if it is optimized or fixed in config,
    # if not use fallback (well's first guide point for x,y) resulting in
    # platform directly above the first guide point (note: kickoff has no fallback):
    px, py, pk = _resolve_platform_coordinates(
        platform_name=well.platform,
        platform_config=platform_config,
        optimized_platform_loc=optimized_platform_loc,
        fallback_xy=(p1.x, p1.y),
    )

    # Create full trajectory including platform and kickoff:
    # - Platform always at z=0 (above last guide point if no platform);
    # - Optional kickoff directly below (same x,y; z=pk if not None).
    x, y, z = [px], [py], [0.0]
    if pk is not None:
        x.append(px)
        y.append(py)
        z.append(pk)

    # Append guide points
    x += [p1.x, p2.x, p3.x]
    y += [p1.y, p2.y, p3.y]
    z += [p1.z, p2.z, p3.z]

    return Trajectory(
        x=np.array(x),
        y=np.array(y),
        z=np.array(z),
    )


def read_trajectories(
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
    missing_wells = [
        f"{point_file}/{well.name}"
        for point_file in itertools.chain(P1, P2, P3)
        for well in wells
        if well.name not in point_files[point_file]
    ]
    if missing_wells:
        raise ValueError(f"Missing wells: {missing_wells}")

    platform_files = _read_files(*PLATFORMS)
    optimized_platform_loc = _map_optimized_platform_locations(
        platforms, platform_files, wells
    )

    return {
        well.name: _read_trajectory(
            well=well,
            platform_config=next(
                (item for item in platforms if item.name == well.platform), None
            ),
            point_files=point_files,
            optimized_platform_loc=optimized_platform_loc,
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
    well_name: str,
    branch: str,
    lateral_files: Dict[str, Any],
) -> Tuple[float, _Point]:
    # Get the true depth:
    z = lateral_files[M1][well_name][branch]

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
    well_name: str,
    branch: str,
    lateral_files: Dict[str, Any],
) -> Tuple[float, Trajectory]:
    # Find the first point of the branch:
    md, mlt_p1 = _find_mlt_p1(well_name, branch, lateral_files)

    # Find the end-point of the branch:
    mlt_p3 = _Point(
        x=lateral_files[M3[0]][well_name][branch],
        y=lateral_files[M3[1]][well_name][branch],
        z=lateral_files[M3[2]][well_name][branch],
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
    wells: Iterable[WellConfig],
) -> Dict[str, Dict[str, Tuple[float, Trajectory]]]:
    lateral_files = _read_lateral_files(wells)
    return (
        {
            well: {
                branch: _read_lateral(well, branch, lateral_files)
                for branch in lateral_files[M1][well]
            }
            for well in lateral_files[M1]
        }
        if M1 in lateral_files
        else {}
    )


def _map_optimized_platform_locations(
    platforms: list[PlatformConfig],
    platform_files: Dict[str, Any],
    wells: Iterable[WellConfig],
) -> Dict[str, Dict[str, Optional[float]]]:
    """
    Create a mapping of platform names to their optimized attributes (x, y, k).
      optimized_loc[name] = {"x": float|None, "y": float|None, "k": float|None}
    Names come from:
      - platforms list (well-trajectory config)
      - wells[].platform (well-trajectory config)
      - keys present in platform_{x,y,k}.json (EVEREST generated optimization files)
    """
    # Names from configs and wells:
    fixed_platform_names = {p.name for p in platforms if platforms is not None}
    well_platform_names = {w.platform for w in wells if w.platform is not None}

    # Names from optimization files:
    optimized_platform_names = set().union(
        *(pf.keys() for pf in platform_files.values())
    )

    undefined_platforms = (
        well_platform_names - fixed_platform_names - optimized_platform_names
    )
    if undefined_platforms:
        msg = (
            f"Some wells refer to undefined platforms: {undefined_platforms}. "
            "Please define them in the `platforms` section of the forward model "
            "configuration (fixed) or specify them in the control section "
            "of the EVEREST config (optimized)."
        )
        logger.error(msg)
        raise SystemExit(msg)

    all_names = fixed_platform_names | well_platform_names | optimized_platform_names

    optimized_loc: Dict[str, Dict[str, Optional[float]]] = {}
    for name in all_names:
        optimized_loc[name] = {
            "x": platform_files.get("platform_x", {}).get(name),
            "y": platform_files.get("platform_y", {}).get(name),
            "k": platform_files.get("platform_k", {}).get(name),
        }
    return optimized_loc


def _resolve_platform_coordinates(
    platform_name: Optional[str],
    platform_config: Optional[PlatformConfig],
    optimized_platform_loc: Dict[str, Dict[str, Optional[float]]],
    fallback_xy: Tuple[float, float],
) -> Tuple[Optional[float], Optional[float], Optional[float]]:
    """
    Resolve (x, y, k) for a platform with precedence:
      1) optimized value if present (opt_val)
      2) fixed value from config if present (cfg_val)
      3) fallback for x/y only (first guide point)
    If both optimized and fixed are present for the same attr, raises SystemExit.
    """
    opt_map = optimized_platform_loc.get(platform_name or "", {})
    if platform_config is not None:
        cfg_x = getattr(platform_config, "x", None)
        cfg_y = getattr(platform_config, "y", None)
        cfg_k = getattr(platform_config, "k", None)
    else:
        cfg_x, cfg_y, cfg_k = (None, None, None)

    def _resolve_platform_coordinate(
        attr: str,
        opt_val: Optional[float],
        cfg_val: Optional[float],
        fallback: Optional[float],
    ) -> Optional[float]:
        if opt_val is not None and cfg_val is not None:
            msg = (
                f"Platform '{platform_name}': attribute '{attr}' is specified both as an "
                f"optimization variable (platform_{attr}.json) and as a fixed value in the "
                f"forward model configuration. Please pick one."
            )
            logger.error(msg)
            raise SystemExit(msg)
        if opt_val is not None:
            return float(opt_val)
        if cfg_val is not None:
            return float(cfg_val)
        if attr in ("x", "y"):
            return float(fallback)
        return None

    px = _resolve_platform_coordinate(
        "x", opt_map.get("x"), cfg_x, fallback=fallback_xy[0]
    )
    py = _resolve_platform_coordinate(
        "y", opt_map.get("y"), cfg_y, fallback=fallback_xy[1]
    )
    pk = _resolve_platform_coordinate("k", opt_map.get("k"), cfg_k, fallback=None)

    return px, py, pk
