import itertools
import logging
from enum import Enum, EnumMeta
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, Optional, Tuple

import numpy

from ..shared.io_utils import load_json
from .models.config import PlatformConfig, ReferencesConfig, ScalesConfig, WellConfig
from .models.data_structs import Trajectory

logger = logging.getLogger("well_trajectory")

P1 = ("p1_x", "p1_y", "p1_z")
P2 = ("p2_a", "p2_b", "p2_c")
P3 = ("p3_x", "p3_y", "p3_z")


class ConstantEnumMeta(EnumMeta):
    def __getattribute__(self, __name: str) -> Any:
        # Return the value directly for enum members
        return (
            attribute.value
            if isinstance(attribute := super().__getattribute__(__name), Enum)  # type: ignore
            else attribute
        )


class PLATFORM_FILES(Enum, metaclass=ConstantEnumMeta):
    X = "platform_x"
    Y = "platform_y"
    Z = "platform_z"
    K = "platform_k"

    @classmethod
    def iter(cls):
        return (x.value for x in cls)


ROUND = 3


def _rescale_point(scale: float, point: float, reference: float):
    return scale * point + reference


def _read_platforms_and_kickoffs(
    trajectory: Dict[str, Any],
    scales: ScalesConfig,
    references: ReferencesConfig,
    platform: PlatformConfig,
) -> Tuple[float, float, float, float]:
    def _file_value(filename: str) -> Optional[float]:
        if filename in trajectory and platform.name in trajectory[filename]:
            logger.warning(
                f"File: {filename}.json found, '{filename.split('_')[1]}' for '{platform.name}' in configuration ignored."
            )
            if filename == PLATFORM_FILES.K and (
                references.k is None or scales.k is None
            ):
                raise ValueError(
                    "Either 'references.k' or 'scales.k' missing in configuration"
                )

            return trajectory[filename][platform.name]

    px, py = (
        (
            _rescale_point(scales.x, p_x, references.x),
            _rescale_point(scales.y, p_y, references.y),
        )
        if (p_x := _file_value(PLATFORM_FILES.X))
        and (p_y := _file_value(PLATFORM_FILES.Y))
        else (
            platform.x,
            platform.y,
        )
    )
    pz = (
        _rescale_point(scales.z, p_z, references.z)
        if (p_z := _file_value(PLATFORM_FILES.Z))
        else platform.z
    )
    kz = (
        _rescale_point(scales.k, k_z, references.k)
        if (k_z := _file_value(PLATFORM_FILES.K))
        else platform.k
    )

    return round(px, ROUND), round(py, ROUND), round(pz, ROUND), round(kz, ROUND)


def _read_files_from_everest() -> Dict[str, Any]:
    return dict(
        itertools.chain(
            (
                (filename, load_json(Path(filename).with_suffix(".json")))
                for filename in itertools.chain(P1, P2, P3)
            ),
            (
                (filename, load_json(Path(filename).with_suffix(".json")))
                for filename in PLATFORM_FILES.iter()
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
    a1, b1, c1 = [round(inputs[key][well], ROUND) for key in P2]
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

        whx, why, whz, koz = _read_platforms_and_kickoffs(
            inputs,
            scales,
            references,
            platform=next(
                platform for platform in platforms if platform.name == well.platform
            ),
        )
        x0, y0, z0 = [round(value, ROUND) for value in generate_rescaled_points(P1)]
        x2, y2, z2 = [round(value, ROUND) for value in generate_rescaled_points(P3)]

        x1, y1, z1 = _construct_midpoint(well.name, inputs, x0, x2, y0, y2, z0, z2)

        return Trajectory(
            x=numpy.array([whx, whx, x0, x1, x2]),
            y=numpy.array([why, why, y0, y1, y2]),
            z=numpy.array([whz, koz, z0, z1, z2]),
        )

    inputs = _read_files_from_everest()

    return {well.name: _construct_trajectory(inputs, well) for well in wells}
