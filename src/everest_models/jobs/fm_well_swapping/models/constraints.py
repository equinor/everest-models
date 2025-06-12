from typing import Tuple, Union

from pydantic import AfterValidator, Field
from typing_extensions import Annotated

from everest_models.jobs.shared.models import ModelConfig
from everest_models.jobs.shared.validators import min_length


class Constraint(ModelConfig):
    fallback_values: Annotated[
        Union[Tuple[float, ...], float, None],
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


class Constraints(ModelConfig):
    state_duration: Annotated[
        Constraint,
        Field(
            description="Constraint information for defining time duration of state swapping intervals"
        ),
    ]
