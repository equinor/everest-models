import datetime
from pathlib import Path
from typing import Any, Dict, Literal, Optional, Tuple, Union

from pydantic import (
    Field,
    FilePath,
    NonNegativeFloat,
    NonNegativeInt,
    PositiveFloat,
    PositiveInt,
    constr,
    validator,
)

from spinningjenny.jobs.shared.models import BaseFrozenConfig, PhaseEnum
from spinningjenny.jobs.shared.validators import validate_eclipse_path


class ScalesConfig(BaseFrozenConfig):
    x: PositiveFloat
    y: PositiveFloat
    z: PositiveFloat
    k: PositiveFloat


class ReferencesConfig(BaseFrozenConfig):
    x: float
    y: float
    z: float
    k: float


class SimpleInterpolationConfig(BaseFrozenConfig):
    type: Literal["simple"]
    length: PositiveInt = 50
    trial_number: NonNegativeInt = 100000
    trial_step: PositiveFloat = 0.01


class ResInsightInterpolationConfig(BaseFrozenConfig):
    type: Literal["resinsight"]
    measured_depth_step: PositiveFloat = 5


class DomainProperty(BaseFrozenConfig):
    key: constr(regex=r"^[^a-z]+$", strict=True)
    min: Optional[float]
    max: Optional[float]


class PerforationConfig(BaseFrozenConfig):
    well: constr(regex=r"^[^a-z]+$", strict=True)
    dynamic: Tuple[DomainProperty, ...] = Field(default_factory=tuple)
    static: Tuple[DomainProperty, ...] = Field(default_factory=tuple)
    formations: Tuple[int, ...] = Field(default_factory=tuple)


class ResInsightConnectionConfig(BaseFrozenConfig):
    type: Literal["resinsight"]
    date: Optional[datetime.date]
    formations_file: FilePath
    perforations: Tuple[PerforationConfig, ...]


class PlatformConfig(BaseFrozenConfig):
    name: str
    x: float
    y: float
    z: float
    k: float


class WellConfig(BaseFrozenConfig):
    name: str
    group: str
    phase: PhaseEnum
    skin: NonNegativeFloat = 0.0
    radius: PositiveFloat = 0.15
    dogleg: PositiveFloat = 4.0
    cost: NonNegativeFloat = 0.0
    platform: Optional[str]


class OutputsConfig(BaseFrozenConfig):
    save_paths: bool = False
    guide_points: Optional[Path]
    geometry: Optional[Path]
    npv_input: Optional[Path]


class ConfigSchema(BaseFrozenConfig):
    scales: ScalesConfig
    references: ReferencesConfig
    interpolation: Union[SimpleInterpolationConfig, ResInsightInterpolationConfig]
    connections: Optional[ResInsightConnectionConfig]
    platforms: Tuple[PlatformConfig, ...] = Field(default_factory=tuple)
    wells: Tuple[WellConfig, ...]
    outputs: Optional[OutputsConfig]
    eclipse_model: Optional[Path]
    resinsight_binary: Optional[FilePath]

    validate_eclipse = validator("eclipse_model", allow_reuse=True)(
        validate_eclipse_path
    )

    @validator("wells", always=True, each_item=True)
    def _validate_wells(cls, well: WellConfig, values: Dict[str, Any]) -> WellConfig:
        if getattr(cls, "_platforms", None) is None:
            cls._platforms = [item.name for item in values["platforms"]]
        if well.platform is not None and well.platform not in cls._platforms:
            raise ValueError(
                f"Platform '{well.platform}' for well '{well.name}' not defined"
            )
        return well
