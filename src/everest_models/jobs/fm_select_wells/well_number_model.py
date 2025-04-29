from pydantic import Field
from typing_extensions import Annotated

from everest_models.jobs.shared.models import ModelConfig


class WellNumber(ModelConfig):
    number_of_wells: Annotated[float, Field(None, description="")]
