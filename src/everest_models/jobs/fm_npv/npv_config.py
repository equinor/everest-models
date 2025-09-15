from typing import Any, Dict, Tuple

from pydantic import Field, model_validator
from typing_extensions import Annotated

from everest_models.jobs.shared.models import Wells
from everest_models.jobs.shared.models.economics import EconomicConfig


class NPVConfig(EconomicConfig):
    summary_keys: Annotated[Tuple[str, ...], Field(description="")]
    wells: Annotated[
        Wells,
        Field(
            default_factory=dict,
            description="",
            examples=["{name: INJ, <field>: <value>}"],
        ),
    ]

    @model_validator(mode="before")
    @classmethod
    def populate_summary_keys(cls, values: Dict[str, Any]):
        if not (values.get("summary_keys") or values.get("prices")):
            raise ValueError("Both summary_keys and prices keys missing")
        values.setdefault("summary_keys", tuple(values["prices"]))
        return values
