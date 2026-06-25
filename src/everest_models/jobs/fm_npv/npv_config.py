from typing import Annotated, Any

from pydantic import Field, model_validator

from everest_models.jobs.shared.models.economics import EconomicConfig


class NPVConfig(EconomicConfig):
    summary_keys: Annotated[tuple[str, ...], Field(description="")]

    @model_validator(mode="before")
    @classmethod
    def populate_summary_keys(cls, values: dict[str, Any]):
        if not (values.get("summary_keys") or values.get("prices")):
            raise ValueError("Both summary_keys and prices keys missing")
        values.setdefault("summary_keys", tuple(values["prices"]))
        return values
