import datetime
import itertools
from typing import ClassVar, Tuple

from pydantic import Field, root_validator, validator

from spinningjenny.jobs.shared.models import BaseFrozenConfig


class _Unavailability(BaseFrozenConfig):
    start_date: ClassVar[datetime.date]
    end_date: ClassVar[datetime.date]
    start: datetime.date
    stop: datetime.date

    @validator("*")
    def is_within_time_range(cls, date):
        if not (cls.start_date <= date <= cls.end_date):
            raise ValueError("Date outside of range")
        return date


class _DrillSubject(BaseFrozenConfig):
    name: str
    wells: Tuple[str, ...]
    unavailability: Tuple[_Unavailability, ...] = Field(default_factory=tuple)


class Slot(_DrillSubject):
    ...


class Rig(_DrillSubject):
    slots: Tuple[str, ...] = Field(default_factory=tuple)
    delay: int = 0

    @validator("delay")
    def is_positive(cls, number):
        if number < 0:
            raise ValueError("delay must be positive integer")
        return number


class DrillPlanConfig(BaseFrozenConfig):
    start_date: datetime.date
    end_date: datetime.date
    rigs: Tuple[Rig, ...]
    slots: Tuple[Slot, ...] = Field(default_factory=tuple)

    def __init__(
        self, start_date: datetime.date, end_date: datetime.date = None, **data
    ) -> None:
        end_date = end_date or datetime.date(3000, 1, 1)
        _Unavailability.start_date = start_date
        _Unavailability.end_date = end_date
        super().__init__(start_date=start_date, end_date=end_date, **data)

    @root_validator
    def all_rig_slots_exist(cls, values):
        if mismatch := set(
            itertools.chain.from_iterable(rig.slots for rig in values.get("rigs", []))
        ).difference(slot.name for slot in values["slots"]):
            raise ValueError(
                f"There are rig(s) with mismatch slot(s):\n\t{', '.join(mismatch)}"
            )
        return values
