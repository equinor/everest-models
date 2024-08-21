import itertools
from datetime import date
from typing import ClassVar, Optional, Tuple

from pydantic import Field, field_validator, model_validator
from typing_extensions import Annotated

from everest_models.jobs.shared.models import ModelConfig


class _Unavailability(ModelConfig):
    start_date: ClassVar[date]
    end_date: ClassVar[date]
    start: Annotated[date, Field(description="")]
    stop: Annotated[date, Field(description="")]

    @field_validator("*")
    @classmethod
    def is_within_time_range(cls, date):
        if not (cls.start_date <= date <= cls.end_date):
            raise ValueError("Date outside of range")
        return date


class _DrillSubject(ModelConfig):
    name: Annotated[str, Field(description="")]
    wells: Annotated[Tuple[str, ...], Field(default_factory=tuple, description="")]
    unavailability: Annotated[
        Tuple[_Unavailability, ...],
        Field(default_factory=tuple, description=""),
    ]


class Slot(_DrillSubject): ...


class Rig(_DrillSubject):
    slots: Annotated[Tuple[str, ...], Field(default_factory=tuple, description="")]
    delay: Annotated[int, Field(default=0, description="", ge=0)]


class DrillPlanConfig(ModelConfig):
    start_date: Annotated[date, Field(description="")]
    end_date: Annotated[date, Field(description="")]
    rigs: Annotated[Tuple[Rig, ...], Field(description="")]
    slots: Annotated[Tuple[Slot, ...], Field(default_factory=tuple, description="")]

    def __init__(
        self, start_date: date, end_date: Optional[date] = None, **data
    ) -> None:
        end_date = end_date or date(3000, 1, 1)
        _Unavailability.start_date = start_date
        _Unavailability.end_date = end_date
        super().__init__(start_date=start_date, end_date=end_date, **data)  # type: ignore

    @model_validator(mode="after")
    def all_rig_slots_exist(self):
        if mismatch := set(
            itertools.chain.from_iterable(rig.slots for rig in self.rigs)
        ).difference(slot.name for slot in self.slots):
            raise ValueError(
                f"There are rig(s) with mismatch slot(s):\n\t{', '.join(mismatch)}"
            )
        return self
