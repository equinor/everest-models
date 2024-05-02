import itertools
from dataclasses import dataclass, field
from typing import List, NamedTuple, Tuple


class WellPriority(NamedTuple):
    drill_time: int
    priority: int


class DayRange(NamedTuple):
    begin: int
    end: int


class AppendMixin:
    def append_day_range(self, begin: int, end: int) -> None:
        self.day_ranges.append(DayRange(begin, end))


@dataclass
class Slot(AppendMixin):
    wells: Tuple[str, ...]
    day_ranges: List[DayRange] = field(default_factory=list)


@dataclass
class Rig(AppendMixin):
    wells: Tuple[str, ...]
    slots: List[str] = field(default_factory=list)
    day_ranges: List[DayRange] = field(default_factory=list)
    delay: int = 0

    @property
    def slot_well_product(self):
        return tuple(itertools.product(self.slots, self.wells))


@dataclass
class Event:
    rig: str
    slot: str
    well: str
    begin: int
    end: int
    completion: int = None

    def __post_init__(self) -> None:
        if self.completion is None:
            self.completion = self.end

    def contains(self, day: int) -> bool:
        return self.begin <= day <= self.end

    def overlaps(self, begin: int, end: int) -> bool:
        return self.end >= begin and self.begin <= end

    @property
    def drill_time(self) -> int:
        return self.end - self.begin
