import re
from datetime import date as Date
from typing import Annotated, Any, Literal, get_args

from pydantic import Field, field_validator

from everest_models.jobs.shared.models import ModelConfig
from everest_models.jobs.shared.models.base_config.introspective import CommentedObject

type Aggregation = Literal["min", "max", "mean", "median"]
type Point = tuple[float, float, float]
type FiniteNumber = Annotated[float, Field(strict=True, allow_inf_nan=False)]
NonEmptyString = Annotated[str, Field(min_length=1)]


class PropertyFilter(ModelConfig):
    name: str = Field(
        pattern=r"^[^\s,]+$", description="Dynamic grid property, for example SGAS."
    )
    threshold: FiniteNumber = Field(
        default=0.0, description="Inclusive lower bound for selecting active cells."
    )
    date: Date | None = Field(
        default=None,
        description="Report date (YYYY-MM-DD). If omitted, use cells qualifying at any report.",
    )

    @field_validator("date", mode="before")
    @classmethod
    def validate_report_date(cls, value: Any) -> Any:
        if value is None or type(value) is Date:
            return value
        if isinstance(value, str) and re.fullmatch(
            r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value.strip()
        ):
            return value.strip()
        raise ValueError("Report date must be in YYYY-MM-DD format")


class Calculation(ModelConfig):
    property: PropertyFilter | None = Field(
        default=None,
        description="Optional property filter. If omitted, use all active cells.",
    )
    aggregation: Aggregation = Field(
        default="min",
        description="Statistic over finite, positive distances: min, max, mean, or median.",
    )
    output: NonEmptyString = Field(description="Filename for the scalar result.")
    multiplier: FiniteNumber = Field(
        default=1.0,
        description="Non-zero factor applied to the scalar and map. Use 0.001 to convert meters to kilometers.",
    )
    verbose: bool | None = Field(
        default=None,
        strict=True,
        description="Write a per-cell distance map; inherits the top-level verbose setting if omitted.",
    )

    @field_validator("multiplier")
    @classmethod
    def validate_multiplier(cls, value: float) -> float:
        if value == 0:
            raise ValueError("Multiplier must be non-zero")
        return value


class FaultCalculation(Calculation):
    type: Literal["fault"] = Field(description="Measure distance to a named fault.")
    name: NonEmptyString = Field(description="Fault name in ResInsight.")


class WellCalculation(Calculation):
    type: Literal["well"] = Field(
        description="Measure distance to a simulation well's connected cells."
    )
    name: NonEmptyString = Field(description="Simulation well name in ResInsight.")


class PolygonCalculation(Calculation):
    type: Literal["polygon"] = Field(
        description="Measure distance to an open polyline."
    )
    points: Annotated[
        tuple[tuple[FiniteNumber, FiniteNumber, FiniteNumber], ...],
        Field(
            min_length=2,
            description="At least two [easting, northing, positive-down depth] points in grid units.",
        ),
    ]


type DistanceCalculation = Annotated[
    FaultCalculation | WellCalculation | PolygonCalculation, Field(discriminator="type")
]


class DistanceConfig(ModelConfig):
    distance_calculations: list[DistanceCalculation] = Field(
        alias="distance-calculations",
        min_length=1,
        description="One or more fault, well, or polygon distance calculations.",
    )
    verbose: bool = Field(
        default=False,
        strict=True,
        description="Default for writing per-cell maps for calculations.",
    )

    @classmethod
    def introspective_data(
        cls, minimal: bool, no_comment: bool = False
    ) -> dict[str, Any]:
        def set_value(fields: dict[str, Any], key: str, value: Any) -> None:
            if isinstance(field := fields[key], CommentedObject):
                field.value = value
            else:
                fields[key] = value

        data = super().introspective_data(minimal, no_comment)
        calculations = []
        for model in (FaultCalculation, WellCalculation, PolygonCalculation):
            fields = model.introspective_data(minimal, no_comment)
            set_value(
                fields, "type", get_args(model.model_fields["type"].annotation)[0]
            )
            if not minimal:
                property_fields = PropertyFilter.introspective_data(minimal, no_comment)
                set_value(property_fields, "date", None)
                set_value(fields, "property", property_fields)
                set_value(fields, "verbose", None)
            if model is PolygonCalculation:
                points = fields["points"]
                if isinstance(points, CommentedObject):
                    points = points.value
                set_value(fields, "points", points * 2)
            calculations.append({"type": fields.pop("type"), **fields})

        set_value(data, "distance_calculations", calculations)
        return {"distance-calculations": data.pop("distance_calculations"), **data}
