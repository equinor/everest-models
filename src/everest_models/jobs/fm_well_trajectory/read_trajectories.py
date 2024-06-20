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


def _read_platform_and_kickoff(
    trajectory: Dict[str, Any],
    scales: ScalesConfig,
    references: ReferencesConfig,
    platform: PlatformConfig,
) -> Tuple[float, float, float, Optional[float]]:
    def _get_point(filename: str, attr: str) -> Optional[float]:
        value = trajectory.get(filename, {}).get(platform.name)
        if value is not None:
            logger.warning(
                f"File: {filename}.json found, overriding '{attr}' "
                f"for '{platform.name}' in configuration."
            )
            scale = getattr(scales, attr)
            ref = getattr(references, attr)
            if scale is None or ref is None:
                raise ValueError(
                    f"Either 'references.{attr}' or 'scales.{attr}' missing in configuration"
                )
            value = _rescale_point(scale, value, ref)
        else:
            # If necessary, get the value from the platform:
            value = getattr(platform, attr)

        if value is not None:
            value = round(value, ROUND)

        return value

    px = _get_point("platform_x", "x")
    py = _get_point("platform_y", "y")
    pz = _get_point("platform_z", "z")
    pk = _get_point("platform_k", "k")

    # px, py and pz are mandatory, pk may be `None`:
    assert px is not None
    assert py is not None
    assert pz is not None

    return px, py, pz, pk


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

        x, y, z = [], [], []

        platform = next(
            (item for item in platforms if item.name == well.platform), None
        )
        if platform is not None:
            px, py, pz, pk = _read_platform_and_kickoff(
                inputs, scales, references, platform
            )
            x.append(px)
            y.append(py)
            z.append(pz)
            if pk is not None:
                x.append(px)
                y.append(py)
                z.append(pk)

        x0, y0, z0 = [round(value, ROUND) for value in generate_rescaled_points(P1)]
        x2, y2, z2 = [round(value, ROUND) for value in generate_rescaled_points(P3)]
        x1, y1, z1 = _construct_midpoint(well.name, inputs, x0, x2, y0, y2, z0, z2)

        return Trajectory(
            x=numpy.array(x + [x0, x1, x2]),
            y=numpy.array(y + [y0, y1, y2]),
            z=numpy.array(z + [z0, z1, z2]),
        )

    inputs = _read_files_from_everest()

    return {well.name: _construct_trajectory(inputs, well) for well in wells}
