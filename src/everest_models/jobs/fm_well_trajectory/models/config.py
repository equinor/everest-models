from __future__ import annotations

import datetime
from pathlib import Path
from typing import Optional, Tuple

from pydantic import (
    AfterValidator,
    Field,
    FilePath,
    PlainSerializer,
    StringConstraints,
    model_validator,
)
from typing_extensions import Annotated

from everest_models.jobs.shared.converters import path_to_str
from everest_models.jobs.shared.models import ModelConfig, PhaseEnum
from everest_models.jobs.shared.validators import validate_eclipse_path


class InterpolationConfig(ModelConfig):
    type: Annotated[
        str,
        Field(
            default="resinsight",
            description="Interpolation type: 'simple' or 'resinsight'.",
            examples="resinsight",
        ),
    ]
    length: Annotated[
        int,
        Field(
            default=50,
            description="Simple interpolation only.",
            examples="100",
            gt=0,
        ),
    ]
    trial_number: Annotated[
        int,
        Field(
            default=100000,
            description="Simple interpolation only.",
            examples="5000",
            ge=0,
        ),
    ]
    trial_step: Annotated[
        float,
        Field(
            default=0.01,
            description="Simple interpolation only.",
            examples="0.02",
            gt=0,
        ),
    ]
    measured_depth_step: Annotated[
        float,
        Field(
            default=5,
            description="ResInsight interpolation only: Step size used in exporting interpolated well trajectories.",
            examples="10",
            gt=0,
        ),
    ]

    @model_validator(mode="after")
    def check_type(self) -> InterpolationConfig:
        fields_set = self.__pydantic_fields_set__ - {"type"}
        if self.type == "resinsight":
            fields = ["length", "trial_number", "trial_step"]
            if fields_set & set(fields):
                msg = f"Interpolation type 'resinsight': fields not allowed: {fields}"
                raise ValueError(msg)
        elif self.type == "simple":
            if fields_set & {"measured_depth_step"}:
                msg = "Interpolation type 'simple': 'measured_depth_step' not allowed"
                raise ValueError(msg)
        else:
            msg = f"Unknown interpolation type: {self.type}"
            raise ValueError(msg)
        return self


class DynamicDomainProperty(ModelConfig):
    key: Annotated[
        str,
        StringConstraints(strip_whitespace=True, strict=True, pattern=r"^[^a-z]+$"),
        Field(
            description="Keyword representing dynamic cell property in flow simulator which will be accepted in filtering.",
            examples="SOIL, SWAT",
        ),
    ]
    min: Annotated[float, Field(description="Minimum value.", examples="0.5")]
    max: Annotated[float, Field(description="Maximum value.", examples="0.3")]
    date: Annotated[
        Optional[datetime.date],
        Field(
            default=None,
            description="Simulation date used for grid perforation filtering based on time dynamic grid flow simulation data.",
        ),
    ]


class StaticDomainProperty(ModelConfig):
    key: Annotated[
        str,
        StringConstraints(strip_whitespace=True, strict=True, pattern=r"^[^a-z]+$"),
        Field(
            description="Keyword for static (initial) cell property in flow simulator which will be accepted in filtering.",
            examples="PORO, PERMX",
        ),
    ]
    min: Annotated[float, Field(description="Minimum value.", examples="0.3, 100")]
    max: Annotated[float, Field(description="Maximum value.", examples="0.4, 30000")]


class PerforationConfig(ModelConfig):
    well: Annotated[
        str,
        StringConstraints(strip_whitespace=True, strict=True, pattern=r"^[^a-z]+$"),
        Field(description="Well name.", examples="PRD1"),
    ]
    dynamic: Annotated[
        Tuple[DynamicDomainProperty, ...],
        Field(default_factory=tuple, description=""),
    ]
    static: Annotated[
        Tuple[StaticDomainProperty, ...],
        Field(default_factory=tuple, description=""),
    ]
    formations: Annotated[
        Tuple[int, ...],
        Field(
            default_factory=tuple,
            description="List of indexes of formations (starting from 0) from formations file which will be accepted in filtering.",
        ),
    ]


class ConnectionConfig(ModelConfig):
    type: Annotated[
        str,
        Field(
            default="resinsight",
            description="Connection type: currently only 'resinsight'.",
            examples="resinsight",
        ),
    ]
    formations_file: Annotated[
        FilePath,
        PlainSerializer(path_to_str, when_used="unless-none"),
        Field(
            description="File defining list of grid based geological formations used for perforation filtering based on formations.",
            examples="/path/to/formations.lyr",
        ),
    ]
    perforations: Annotated[Tuple[PerforationConfig, ...], Field(description="")]

    @model_validator(mode="after")
    def check_type(self) -> ConnectionConfig:
        if self.type != "resinsight":
            msg = f"Unknown interpolation type: {self.type}"
            raise ValueError(msg)
        return self

    @model_validator(mode="before")
    def check_deprecated_field(cls, data):
        if "date" in data:
            raise ValueError(
                (
                    "The 'date' field is no longer allowed at this level.\n"
                    "It is only required for dynamic perforations. "
                    "Move it to each relevant dynamic perforation instead.\n"
                    "Static perforations do not require a date and are read from the initial state."
                )
            )
        return data


class PlatformConfig(ModelConfig):
    name: Annotated[
        str,
        Field(
            description="Name for platform.",
            examples="PLATF1",
        ),
    ]
    x: Annotated[
        float,
        Field(
            description="Coordinate x of the platform at depth 0.",
            examples="5000.0",
        ),
    ]
    y: Annotated[
        float,
        Field(
            description="Coordinate y of the platform at depth 0.",
            examples="5000.0",
        ),
    ]
    k: Annotated[
        float,
        Field(
            default=None,
            description="Coordinate z of the kick-off (directly under the platform.)",
            examples="300.0",
        ),
    ]


class WellConfig(ModelConfig):
    name: Annotated[
        str,
        Field(
            description="Well name.",
            examples="PRD1",
        ),
    ]
    group: Annotated[
        str,
        Field(
            description="Well group name to be assigned to well in flow simulator",
            examples="G1",
        ),
    ]
    phase: Annotated[
        PhaseEnum,
        Field(
            description="Well phase name to be assigned to well in flow simulator.",
            examples="WATER, OIL, GAS",
        ),
    ]
    skin: Annotated[
        float,
        Field(
            default=0.0,
            description="Well skin value to be assigned to well in flow simulator.",
            examples="0.2",
            ge=0,
        ),
    ]
    radius: Annotated[
        float,
        Field(
            default=0.15,
            description="Well radius value to be assigned to well in flow simulator.",
            examples="0.33",
            gt=0,
        ),
    ]
    dogleg: Annotated[
        float,
        Field(
            default=4.0,
            description="Well maximum dogleg used for interpolating well trajectory.",
            examples="5.0",
            gt=0,
        ),
    ]
    cost: Annotated[
        float,
        Field(
            default=0.0,
            description="Drilling cost per kilometer. Used to update well costs in the input file for NPV.",
            examples="4000000",
            ge=0,
        ),
    ]
    platform: Annotated[
        str,
        Field(
            default=None,
            description="Name of the platform selected for the well.",
            examples="PLATF1",
        ),
    ]


class ConfigSchema(ModelConfig):
    interpolation: Annotated[
        InterpolationConfig,
        Field(
            description="Options related to interpolation of guide points.",
        ),
    ]
    connections: Annotated[
        ConnectionConfig,
        Field(
            description="Options related to the connections.",
            default=None,
        ),
    ]
    platforms: Annotated[
        Tuple[PlatformConfig, ...],
        Field(
            default_factory=tuple,
            description="Configuration of the platforms.",
        ),
    ]
    wells: Annotated[
        Tuple[WellConfig, ...],
        Field(
            description="Configuration of the wells.",
        ),
    ]
    eclipse_model: Annotated[
        Path,
        AfterValidator(validate_eclipse_path),
        Field(
            description="Path and name of the flow simulation grid model. Ignored if passed as argument instead.",
            examples="/path/to/MODEL.EGRID",
            default=None,
        ),
    ]
    resinsight_binary: Annotated[
        FilePath,
        Field(
            default=None,
            description="Path to ResInsight executable. Defaults to system path.",
            examples="/path/to/ResInsight",
        ),
    ]
    npv_input_file: Annotated[
        FilePath,
        Field(
            default=None,
            description="Path to YAML file (input to fm_npv) used to update the well costs.",
            examples="/path/to/npv_input.yml",
        ),
    ]
