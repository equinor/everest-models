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
    x: Annotated[
        float,
        Field(
            description="Scaling length for coordinate x for the guide points.",
            gt=0,
        ),
    ]
    y: Annotated[
        float,
        Field(
            description="Scaling length for coordinate y for the guide points.",
            gt=0,
        ),
    ]
    z: Annotated[
        float,
        Field(
            description="Scaling length for coordinate z (positive depth) for the guide points.",
            gt=0,
        ),
    ]
    k: Annotated[
        float,
        Field(
            default=None,
            description="Scaling length for z (positive depth) for the kick-off point.",
            gt=0,
        ),
    ]


class ReferencesConfig(ModelConfig):
    x: Annotated[
        float,
        Field(
            description="Coordinate x for reference point used in scaling of guide points."
        ),
    ]
    y: Annotated[
        float,
        Field(
            description="Coordinate y for reference point used in scaling of guide points."
        ),
    ]
    z: Annotated[
        float,
        Field(
            description="Coordinate z for reference point used in scaling of guide points."
        ),
    ]
    k: Annotated[
        float,
        Field(
            default=None,
            description="Coordinate z for reference point used in scaling of kick-off point.",
        ),
    ]


class SimpleInterpolationConfig(ModelConfig):
    type: Literal["simple"]
    length: Annotated[int, Field(default=50, description="", gt=0)]
    trial_number: Annotated[int, Field(default=100000, description="", ge=0)]
    trial_step: Annotated[float, Field(default=0.01, description="", gt=0)]


class ResInsightInterpolationConfig(ModelConfig):
    type: Literal["resinsight"]
    measured_depth_step: Annotated[
        float,
        Field(
            default=5,
            description="'Step size used in exporting interpolated well trajectories.",
            gt=0,
        ),
    ]


class DomainProperty(ModelConfig):
    key: Annotated[
        str,
        StringConstraints(strip_whitespace=True, strict=True, pattern=r"^[^a-z]+$"),
        Field(
            description="Keyword representing a cell property in flow simulator which will be accepted in filtering."
        ),
    ]
    min: Annotated[float, Field(description="Minimum value.")]
    max: Annotated[float, Field(description="Maximum value.")]


class PerforationConfig(ModelConfig):
    well: Annotated[
        str,
        StringConstraints(strip_whitespace=True, strict=True, pattern=r"^[^a-z]+$"),
        Field(description="Well name."),
    ]
    dynamic: Annotated[
        Tuple[DomainProperty, ...],
        Field(default_factory=tuple, description=""),
    ]
    static: Annotated[
        Tuple[DomainProperty, ...],
        Field(default_factory=tuple, description=""),
    ]
    formations: Annotated[
        Tuple[int, ...],
        Field(
            default_factory=tuple,
            description="List of indexes of formations (starting from 0) from formations file which will be accepted in filtering.",
        ),
    ]


class ResInsightConnectionConfig(ModelConfig):
    type: Literal["resinsight"]
    date: Annotated[
        datetime.date,
        Field(
            description="Simulation date used for grid perforation filtering based on time dynamic grid flow simulation data."
        ),
    ]
    formations_file: Annotated[
        FilePath,
        PlainSerializer(path_to_str, when_used="unless-none"),
        Field(
            description="File defining list of grid based geological formations used for perforation filtering based on formations."
        ),
    ]
    perforations: Annotated[Tuple[PerforationConfig, ...], Field(description="")]


class PlatformConfig(ModelConfig):
    name: Annotated[str, Field(description="Name for platform.")]
    x: Annotated[float, Field(description="Coordinate x of the platform at depth 0.")]
    y: Annotated[float, Field(description="Coordinate y of the platform at depth 0.")]
    k: Annotated[
        float,
        Field(
            default=None,
            description="Coordinate z of the kick-off (directly under the platform.)",
        ),
    ]


class WellConfig(ModelConfig):
    name: Annotated[str, Field(description="Well name.")]
    group: Annotated[
        str,
        Field(description="Well group name to be assigned to well in flow simulator"),
    ]
    phase: Annotated[
        PhaseEnum,
        Field(description="Well phase name to be assigned to well in flow simulator."),
    ]
    skin: Annotated[
        float,
        Field(
            default=0.0,
            description="Well skin value to be assigned to well in flow simulator.",
            ge=0,
        ),
    ]
    radius: Annotated[
        float,
        Field(
            default=0.15,
            description="Well radius value to be assigned to well in flow simulator.",
            gt=0,
        ),
    ]
    dogleg: Annotated[
        float,
        Field(
            default=4.0,
            description="Well maximum dogleg used for interpolating well trajectory.",
            gt=0,
        ),
    ]
    cost: Annotated[
        float,
        Field(
            default=0.0,
            description="Drilling cost per kilometer. Used to update well costs in the input file for NPV.",
            ge=0,
        ),
    ]
    platform: Annotated[
        str,
        Field(default=None, description="Name of the platform selected for the well."),
    ]


class ConfigSchema(ModelConfig):
    scales: Annotated[ScalesConfig, Field(description="")]
    references: Annotated[ReferencesConfig, Field(description="")]
    interpolation: Annotated[
        Union[SimpleInterpolationConfig, ResInsightInterpolationConfig],
        Field(description="Options related to interpolation of guide points."),
    ]
    connections: Annotated[
        ResInsightConnectionConfig, Field(description="", default=None)
    ]
    platforms: Annotated[
        Tuple[PlatformConfig, ...], Field(default_factory=tuple, description="")
    ]
    wells: Annotated[Tuple[WellConfig, ...], Field(description="")]
    eclipse_model: Annotated[
        Path,
        AfterValidator(validate_eclipse_path),
        Field(
            description="Path and name of the flow simulation grid model. Ignored if passed as argument instead.",
            default=None,
        ),
    ]
    resinsight_binary: Annotated[
        FilePath,
        Field(
            default=None,
            description="Path to ResInsight executable. Defaults to system path.",
        ),
    ]
    npv_input_file: Annotated[
        FilePath,
        Field(
            default=None,
            description="Path to YAML file (input to fm_npv) used to update the well costs.",
        ),
    ]

    @field_validator("wells")
    def _validate_wells(
        cls, wells: Tuple[WellConfig, ...], values: ValidationInfo
    ) -> Tuple[WellConfig, ...]:
        for well in wells:
            _platforms = [item.name for item in values.data["platforms"]]
            if well.platform is not None and well.platform not in _platforms:
                raise ValueError(
                    f"Platform '{well.platform}' for well '{well.name}' not defined"
                )
        return wells
