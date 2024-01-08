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
    StringConstraints,
    field_validator,
)
from typing_extensions import Annotated

from everest_models.jobs.shared.models import BaseFrozenConfig, PhaseEnum
from everest_models.jobs.shared.validators import validate_eclipse_path


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
    key: Annotated[str, StringConstraints(pattern=r"^[^a-z]+$", strict=True)]
    min: Optional[float]
    max: Optional[float]


class PerforationConfig(BaseFrozenConfig):
    well: Annotated[str, StringConstraints(pattern=r"^[^a-z]+$", strict=True)]
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
    platform: Optional[str] = None


class OutputsConfig(BaseFrozenConfig):
    save_paths: bool = False
    guide_points: Optional[Path] = None
    geometry: Optional[Path] = None
    npv_input: Optional[Path] = None


class ConfigSchema(BaseFrozenConfig):
    scales: ScalesConfig
    references: ReferencesConfig
    interpolation: Union[SimpleInterpolationConfig, ResInsightInterpolationConfig]
    connections: Optional[ResInsightConnectionConfig] = None
    platforms: Tuple[PlatformConfig, ...] = Field(default_factory=tuple)
    wells: Tuple[WellConfig, ...]
    outputs: Optional[OutputsConfig] = None
    eclipse_model: Optional[Path] = None
    resinsight_binary: Optional[FilePath] = None

    validate_eclipse = field_validator("eclipse_model")(validate_eclipse_path)

    @field_validator("wells")
    def _validate_wells(cls, wells: WellConfig, values: Dict[str, Any]) -> WellConfig:
        if getattr(cls, "_platforms", None) is None:
            cls._platforms = [item.name for item in values.data["platforms"]]
        for well in wells:
            if well.platform is not None and well.platform not in cls._platforms:
                raise ValueError(
                    f"Platform '{well.platform}' for well '{well.name}' not defined"
                )
        return wells
