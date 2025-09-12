from pydantic import Field
from typing_extensions import Annotated

from everest_models.jobs.shared.models import ModelConfig, Wells


class DrillDatePlannerConfig(ModelConfig):
    wells: Annotated[
        Wells,
        Field(
            default_factory=dict,
            description="",
            examples=["{name: INJ, <field>: <value>}"],
        ),
    ]
