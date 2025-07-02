from typing import NamedTuple, Sequence, Tuple, Union

from pydantic import AfterValidator, Field, field_validator
from typing_extensions import Annotated

from everest_models.jobs.shared import rescale_value
from everest_models.jobs.shared.models import ModelConfig
from everest_models.jobs.shared.validators import min_length


class _Bound(NamedTuple):
    min: float
    max: float


class _Scaling(ModelConfig):
    source: Annotated[
        _Bound,
        Field(
            description="[min, max] values for scaling source",
            examples=[[0, 1], [0.0, 1.0], [0.5, 2.0]],
        ),
    ]
    target: Annotated[
        _Bound,
        Field(
            description="[min, max] values for scaling target (in days)",
            examples=[[0, 500], [100.0, 400.0], [1.5e2, 1.0e3]],
        ),
    ]

    @field_validator("*", mode="after")
    def valid_bound(cls, bound: _Bound) -> _Bound:
        if bound.min > bound.max:
            raise ValueError(
                f"[min, max], where min cannot be greater than max: {list(bound)}"
            )
        return bound


class _Constraint(ModelConfig):
    fallback_values: Annotated[
        Union[Tuple[float, ...], float],
        AfterValidator(min_length(1)),
        Field(
            default=None,
            description=(
                "Fallback values for each iteration if constraint JSON file is missing\n"
                "Note: If a single number is given, all swapping intervals will be assigned that time duration"
            ),
            examples=[[150.0, 200, 5e5], 200.0],
        ),
    ]
    scaling: Annotated[
        _Scaling,
        Field(
            description="Scaling factors specified by user to define scaled initial_guess values for state_duration control variable in Everest configuration file.\n"
            "Given these factors the forward model will rescale the state_duration values into physical values (in days)",
        ),
    ]


class Constraints(ModelConfig):
    state_duration: Annotated[
        _Constraint,
        Field(
            description="Constraint information for defining time duration of state swapping intervals"
        ),
    ]

    def rescale(self, constraints: Sequence[float]) -> Tuple[float, ...]:
        return tuple(
            round(
                rescale_value(
                    value,
                    self.state_duration.scaling.source.min,
                    self.state_duration.scaling.source.max,
                    self.state_duration.scaling.target.min,
                    self.state_duration.scaling.target.max,
                )
            )
            for value in constraints
        )
