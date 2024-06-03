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
        Field(description="[min, max] values for scaling source"),
    ]
    target: Annotated[
        _Bound,
        Field(description="[min, max] values for scaling target"),
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
        Union[Tuple[int, ...], int],
        AfterValidator(min_length(1)),
        Field(
            default=None,
            description=(
                "Fallback values for each iteration if constraint json file is missing\n"
                "Note: If a int is given, all iterations will be initialize to that "
                "string"
            ),
            examples=[[150, 200, 500], 200],
        ),
    ]
    scaling: Annotated[
        _Scaling,
        Field(
            description="Scaling data used by everest for producing constraint files,\n"
            "given these values this forward model will rescale the constraints"
        ),
    ]


class Constraints(ModelConfig):
    state_duration: Annotated[
        _Constraint,
        Field(
            description="Constraint information for the time duration of any given "
            "state per iteraton"
        ),
    ]

    def rescale(self, constraints: Union[Sequence[float], int]) -> Tuple[int, ...]:
        if isinstance(constraints, int):
            if isinstance(self.state_duration.fallback_values, int):
                if not constraints:
                    raise ValueError(
                        "Unable to build state duration fallback constraints."
                    )
                return (self.state_duration.fallback_values,) * constraints
            return self.state_duration.fallback_values

        scaling = self.state_duration.scaling
        return tuple(
            round(
                rescale_value(
                    value,
                    scaling.source.min,
                    scaling.source.max,
                    scaling.target.min,
                    scaling.target.max,
                )
            )
            for value in constraints
        )
