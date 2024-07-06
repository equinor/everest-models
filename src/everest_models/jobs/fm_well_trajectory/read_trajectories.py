import itertools
import logging
from pathlib import Path
from typing import Any, Dict, Final, Iterable, NamedTuple, Optional, Tuple

import numpy

from ..shared.io_utils import load_json
from .models.config import PlatformConfig, ReferencesConfig, ScalesConfig, WellConfig
from .models.data_structs import Trajectory

logger = logging.getLogger("well_trajectory")

P1: Final = tuple(f"p1_{tag}" for tag in ("x", "y", "z"))
P2: Final = tuple(f"p2_{tag}" for tag in ("a", "b", "c"))
P3: Final = tuple(f"p3_{tag}" for tag in ("x", "y", "z"))
PLATFORMS: Final = tuple(f"platform_{tag}" for tag in ("x", "y", "k"))

ROUND = 3


class _Point(NamedTuple):
    x: float
    y: float
    z: float


def _rescale(point: float, scale: float, reference: float):
    return scale * point + reference


def _read_files(*args: Tuple[str, ...]) -> Dict[str, Any]:
    return {
        filename: (load_json(Path(filename).with_suffix(".json")))
        for filename in itertools.chain(*args)
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

        if value is not None:
            value = round(value, ROUND)

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
        x=round(_rescale(px, scales.x, references.x), ROUND),
        y=round(_rescale(py, scales.y, references.y), ROUND),
        z=round(_rescale(pz, scales.z, references.z), ROUND),
    )


def _construct_midpoint(
    well: str, input_files: Dict[str, Any], p1: _Point, p3: _Point
) -> Tuple[float, float, float]:
    a, b, c = [round(input_files[key][well], ROUND) for key in P2]
    return _Point._make(
        numpy.round(
            [
                b * (p3.y - p1.y) + a * (p3.x - p1.x) + p1.x,
                b * (p1.x - p3.x) + a * (p3.y - p1.y) + p1.y,
                p3.z + c * (p1.z - p3.z),
            ],
            ROUND,
        )
    )


def _read_trajectory(
    scales: ScalesConfig,
    references: ReferencesConfig,
    well: WellConfig,
    platform_config: Optional[PlatformConfig],
    point_files: Dict[str, Any],
    platform_files: Dict[str, Any],
) -> Trajectory:
    p1 = _get_rescaled_point(P1, point_files, well.name, scales, references)
    p3 = _get_rescaled_point(P3, point_files, well.name, scales, references)
    p2 = _construct_midpoint(well.name, point_files, p1, p3)

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
        x=numpy.array(x + [p1.x, p2.x, p3.x]),
        y=numpy.array(y + [p1.y, p2.y, p3.y]),
        z=numpy.array(z + [p1.z, p2.z, p3.z]),
    )


def read_trajectories(
    scales: ScalesConfig,
    references: ReferencesConfig,
    wells: Iterable[WellConfig],
    platforms: Iterable[PlatformConfig],
) -> Dict[str, Trajectory]:
    point_files = _read_files(P1, P2, P3)
    missing_files = [
        point_file
        for point_file in itertools.chain(P1, P2, P3)
        if point_file not in point_files
    ]
    if missing_files:
        raise ValueError(f"Missing point files: {missing_files}")

    platform_files = _read_files(PLATFORMS)

    return {
        well.name: _read_trajectory(
            scales=scales,
            references=references,
            well=well,
            platform_config=next(
                (item for item in platforms if item.name == well.platform), None
            ),
            point_files=point_files,
            platform_files=platform_files,
        )
        for well in wells
    }
