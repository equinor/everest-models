import datetime
import itertools
from typing import Any, Dict, List

from everest_models.jobs.fm_drill_planner.data import DayRange, Rig, Slot, WellPriority
from everest_models.jobs.fm_drill_planner.manager.field_manager import FieldManager
from everest_models.jobs.fm_drill_planner.models import DrillPlanConfig, Wells


class FieldManagerBuilder:
    def __init__(self) -> None:
        self._reset()

    def _reset(self) -> None:
        self._manager: FieldManager = None
        self._attributes: Dict[str, Any] = {}
        self._errors: List[str] = []

    @property
    def manager(self) -> FieldManager:
        if manager := self._manager:
            self._reset()
        return manager

    def _missing_attributes(self, *args) -> None:
        if missing := ", ".join(set(args).difference(self._attributes)):
            raise AttributeError(f"Missing FieldManager Attribute(s):\n\t{missing}")

    def parse_well_priority(
        self, wells: Wells, optimizer: Dict[str, int]
    ) -> "FieldManagerBuilder":
        self._attributes.setdefault(
            "wells",
            {
                well.name: WellPriority(
                    priority=optimizer[well.name], drill_time=well.drill_time
                )
                for well in wells
            },
        )
        return self

    def parse_config(
        self, config: DrillPlanConfig, ignore_end_date: bool
    ) -> "FieldManagerBuilder":
        start_date = config.start_date

        def day_range(unavailable):
            return DayRange(
                (unavailable.start - start_date).days,
                (unavailable.stop - start_date).days,
            )

        self._attributes.update(
            {
                "rigs": {
                    rig.name: Rig(
                        rig.wells,
                        list(rig.slots),
                        [day_range(unavailable) for unavailable in rig.unavailability],
                        rig.delay,
                    )
                    for rig in config.rigs
                },
                "slots": {
                    slot.name: Slot(
                        slot.wells,
                        [day_range(unavailable) for unavailable in slot.unavailability],
                    )
                    for slot in config.slots
                },
                "horizon": (
                    (datetime.date(3000, 1, 1) if ignore_end_date else config.end_date)
                    - start_date
                ).days,
            }
        )
        return self

    def add_missing_slots(self) -> "FieldManagerBuilder":
        self._missing_attributes("slots", "rigs")
        slot_names = tuple(self._attributes["slots"])

        def unique_slot_name(rig_name):
            """Generate unique slot names based on the rig name and an index."""
            iteration = 0
            while True:
                if (slot := f"_{rig_name}_slot_{iteration}") not in slot_names:
                    yield slot
                iteration += 1

        def unique_slots(rig_name, rig):
            for well_name, slot_name in zip(
                rig.wells, unique_slot_name(rig_name), strict=False
            ):
                rig.slots.append(slot_name)
                yield slot_name, Slot(wells=(well_name,))

        self._attributes["slots"].update(
            dict(
                itertools.chain.from_iterable(
                    unique_slots(rig_name, rig)
                    for rig_name, rig in self._attributes["rigs"].items()
                    if not rig.slots
                )
            )
        )

        return self

    def _no_slot_combination_wells(self):
        def _slot_combination_exist(well_name: str) -> bool:
            slots_ = {
                name
                for name, slot in self._attributes["slots"].items()
                if well_name in slot.wells
            }
            return any(
                slots_.intersection(rig.slots)
                for rig in self._attributes["rigs"].values()
                if well_name in rig.wells
            )

        return [
            well_name
            for well_name in iter(self._attributes["wells"])
            if not _slot_combination_exist(well_name)
        ]

    def build(self, lint: bool) -> "FieldManagerBuilder":
        self._missing_attributes("wells", "slots", "rigs", "horizon")
        if well_names := ", ".join(self._no_slot_combination_wells()):
            raise ValueError(f"No slot combination available for:\n\t{well_names}")
        if not lint:
            self._manager = FieldManager(**self._attributes)
        return self


def get_field_manager(
    config: DrillPlanConfig,
    wells: Wells,
    optimizer: Dict[str, int],
    ignore_end_date: bool,
    skip_creation: bool,
) -> FieldManager:
    """Construct a parsed and valid FieldManager.

    Args:
        config (DrillPlanConfig): parsed and validated drill plan configuration
        wells (Wells): parsed and validated wells.json
        optimizer (Dict[str, int]): wells priorities
        ignore_end_date (bool): ignore drill plan configuration end date
        skip_creation (bool): terminate build process, without FieldManager creation

    Returns:
        FieldManager: A rig field event manager
    """
    return (
        FieldManagerBuilder()
        .parse_well_priority(wells, optimizer)
        .parse_config(config, ignore_end_date)
        .add_missing_slots()
        .build(skip_creation)
        .manager
    )
