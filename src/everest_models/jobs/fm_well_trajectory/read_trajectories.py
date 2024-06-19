import itertools
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, Optional, Tuple

import numpy

from ..shared.io_utils import load_json
from .models.config import PlatformConfig, ReferencesConfig, ScalesConfig, WellConfig
from .models.data_structs import Trajectory

X1 = ("x1_x", "x1_y", "x1_z")
X2 = ("x2_a", "x2_b", "x2_c")
X3 = ("x3_x", "x3_y", "x3_z")

OPTIONAL_FILES = [
    "p_x",
    "p_y",
    "p_z",
    "k_z",
]
ROUND = 3


def _rescale_point(scale: float, point: float, reference: float):
    return scale * point + reference


def _read_platforms_and_kickoffs(
    trajectory: Dict[str, Any],
    scales: ScalesConfig,
    references: ReferencesConfig,
    well_name: str,
    platform: Optional[PlatformConfig],
) -> Tuple[float, float, float, float]:
    def _get_point(key: str, attr: str) -> Optional[float]:
        value = trajectory.get(key, {}).get(well_name)
        if value is not None:
            value = _rescale_point(
                getattr(scales, attr), value, getattr(references, attr)
            )
        if value is None and platform is not None:
            value = getattr(platform, attr)
        if value is not None:
            value = round(value, ROUND)
        return value

    px = _get_point("p_x", "x")
    py = _get_point("p_y", "y")
    pz = _get_point("p_z", "z")
    kz = _get_point("k_z", "k")

    return px, py, pz, kz


def _read_files_from_everest() -> Dict[str, Any]:
    return dict(
        itertools.chain(
            (
                (filename, load_json(Path(filename).with_suffix(".json")))
                for filename in itertools.chain(X1, X2, X3)
            ),
            (
                (filename, load_json(filename))
                for filename in OPTIONAL_FILES
                if Path(filename).with_suffix(".json").exists()
            ),
        )
    )


def _construct_midpoint(
    well: str,
    inputs: Dict[str, Any],
    x0: float,
    x2: float,
    y0: float,
    y2: float,
    z0: float,
    z2: float,
) -> Tuple[float, float, float]:
    a1, b1, c1 = [round(inputs[key][well], ROUND) for key in X2]
    return tuple(
        numpy.around(
            [
                b1 * (y2 - y0) + a1 * (x2 - x0) + x0,
                b1 * (x0 - x2) + a1 * (y2 - y0) + y0,
                z2 + c1 * (z0 - z2),
            ],
            ROUND,
        )
    )


def read_trajectories(
    scales: ScalesConfig,
    references: ReferencesConfig,
    wells: WellConfig,
    platforms: Iterable[PlatformConfig],
) -> Dict[str, Trajectory]:
    def _construct_trajectory(inputs: Dict[str, Any], well: WellConfig) -> Trajectory:
        def generate_rescaled_points(values: Iterable[str]) -> Iterator[float]:
            return (
                _rescale_point(scale, inputs[value][well.name], reference)
                for value, scale, reference in zip(
                    values,
                    scales.model_dump(exclude={"k"}).values(),
                    references.model_dump(exclude={"k"}).values(),
                )
            )

        x0, y0, z0 = [round(value, ROUND) for value in generate_rescaled_points(X1)]
        x2, y2, z2 = [round(value, ROUND) for value in generate_rescaled_points(X3)]
        x1, y1, z1 = _construct_midpoint(well.name, inputs, x0, x2, y0, y2, z0, z2)
        whx, why, whz, koz = _read_platforms_and_kickoffs(
            inputs,
            scales,
            references,
            well.name,
            platform=next(
                (item for item in platforms if item.name == well.platform), None
            ),
        )

        x, y, z = [], [], []
        if whx is not None:
            if why is None or whz is None:
                raise RuntimeError(
                    "Incomplete platform location, some coordinates are missing."
                )
            x.append(whx)
            y.append(why)
            z.append(whz)
        if koz is not None:
            if whx is None or why is None:
                raise RuntimeError(
                    "A kickoff is defined, but the platform coordinates are missing or incomplete."
                )
            x.append(whx)
            y.append(why)
            z.append(koz)

        return Trajectory(
            x=numpy.array(x + [x0, x1, x2]),
            y=numpy.array(y + [y0, y1, y2]),
            z=numpy.array(z + [z0, z1, z2]),
        )

    inputs = _read_files_from_everest()

    return {well.name: _construct_trajectory(inputs, well) for well in wells}
