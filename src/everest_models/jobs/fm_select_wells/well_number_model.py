from typing import Annotated

from pydantic import Field

from everest_models.jobs.shared.models import ModelConfig


class WellNumber(ModelConfig):
    number_of_wells: Annotated[float, Field(None, description="")]
