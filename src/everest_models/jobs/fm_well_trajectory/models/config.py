import datetime
from pathlib import Path
from typing import Literal, Tuple, Union

from pydantic import (
    AfterValidator,
    Field,
    FilePath,
    PlainSerializer,
    StringConstraints,
    ValidationInfo,
    field_validator,
)
from typing_extensions import Annotated

from everest_models.jobs.shared.converters import path_to_str
from everest_models.jobs.shared.models import ModelConfig, PhaseEnum
from everest_models.jobs.shared.validators import validate_eclipse_path


class ScalesConfig(ModelConfig):
    x: Annotated[float, Field(description="", gt=0)]
    y: Annotated[float, Field(description="", gt=0)]
    z: Annotated[float, Field(description="", gt=0)]
    k: Annotated[float, Field(description="", gt=0)]


class ReferencesConfig(ModelConfig):
    x: Annotated[float, Field(description="")]
    y: Annotated[float, Field(description="")]
    z: Annotated[float, Field(description="")]
    k: Annotated[float, Field(description="")]


class SimpleInterpolationConfig(ModelConfig):
    type: Literal["simple"]
    length: Annotated[int, Field(default=50, description="", gt=0)]
    trial_number: Annotated[int, Field(default=100000, description="", ge=0)]
    trial_step: Annotated[float, Field(default=0.01, description="", gt=0)]


class ResInsightInterpolationConfig(ModelConfig):
    type: Literal["resinsight"]
    measured_depth_step: Annotated[float, Field(default=5, description="", gt=0)]


class DomainProperty(ModelConfig):
    key: Annotated[
        str, StringConstraints(strip_whitespace=True, strict=True, pattern=r"^[^a-z]+$")
    ]
    min: Annotated[float, Field(description="")]
    max: Annotated[float, Field(description="")]


class PerforationConfig(ModelConfig):
    well: Annotated[
        str, StringConstraints(strip_whitespace=True, strict=True, pattern=r"^[^a-z]+$")
    ]
    dynamic: Annotated[
        Tuple[DomainProperty, ...],
        Field(default_factory=tuple, description=""),
    ]
    static: Annotated[
        Tuple[DomainProperty, ...],
        Field(default_factory=tuple, description=""),
    ]
    formations: Annotated[Tuple[int, ...], Field(default_factory=tuple, description="")]


class ResInsightConnectionConfig(ModelConfig):
    type: Literal["resinsight"]
    date: Annotated[datetime.date, Field(description="")]
    formations_file: Annotated[
        FilePath,
        PlainSerializer(path_to_str, when_used="unless-none"),
        Field(description=""),
    ]
    perforations: Annotated[Tuple[PerforationConfig, ...], Field(description="")]


class PlatformConfig(ModelConfig):
    name: str
    x: Annotated[float, Field(description="")]
    y: Annotated[float, Field(description="")]
    z: Annotated[float, Field(default=0.0, description="")]
    k: Annotated[float, Field(description="")]


class WellConfig(ModelConfig):
    name: Annotated[str, Field(description="")]
    group: Annotated[str, Field(description="")]
    phase: Annotated[PhaseEnum, Field(description="")]
    skin: Annotated[float, Field(default=0.0, description="", ge=0)]
    radius: Annotated[float, Field(default=0.15, description="", gt=0)]
    dogleg: Annotated[float, Field(default=4.0, description="", gt=0)]
    cost: Annotated[float, Field(default=0.0, description="", ge=0)]
    platform: Annotated[str, Field(default=None, description="")]


class OutputsConfig(ModelConfig):
    save_paths: Annotated[bool, Field(default=False, description="")]
    guide_points: Annotated[Path, Field(default=None, description="")]
    geometry: Annotated[Path, Field(default=None, description="")]
    npv_input: Annotated[Path, Field(default=None, description="")]


class ConfigSchema(ModelConfig):
    scales: Annotated[ScalesConfig, Field(description="")]
    references: Annotated[ReferencesConfig, Field(description="")]
    interpolation: Annotated[
        Union[SimpleInterpolationConfig, ResInsightInterpolationConfig],
        Field(description=""),
    ]
    connections: Annotated[
        ResInsightConnectionConfig, Field(description="", default=None)
    ]
    platforms: Annotated[
        Tuple[PlatformConfig, ...], Field(default_factory=tuple, description="")
    ]
    wells: Annotated[Tuple[WellConfig, ...], Field(description="")]
    outputs: Annotated[OutputsConfig, Field(description="", default=None)]
    eclipse_model: Annotated[
        Path,
        AfterValidator(validate_eclipse_path),
        Field(description="", default=None),
    ]
    resinsight_binary: Annotated[FilePath, Field(default=None, description="")]

    @field_validator("wells")
    def _validate_wells(
        cls, wells: Tuple[WellConfig, ...], values: ValidationInfo
    ) -> Tuple[WellConfig, ...]:
        for well in wells:
            if getattr(cls, "_platforms", None) is None:
                cls._platforms = [item.name for item in values.data["platforms"]]
            if well.platform is not None and well.platform not in cls._platforms:
                raise ValueError(
                    f"Platform '{well.platform}' for well '{well.name}' not defined"
                )
        return wells
