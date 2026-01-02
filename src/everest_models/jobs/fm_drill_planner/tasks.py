from datetime import date, timedelta
from typing import Dict

from everest_models.jobs.fm_drill_planner.manager.field_manager import FieldManager
from everest_models.jobs.fm_drill_planner.models.wells import Well
from everest_models.jobs.shared.models.wells import Operation


def orchestrate_drill_schedule(
    manager: FieldManager, wells: Dict[str, Well], start_date: date, time_limit: int
) -> None:
    def date(days):
        return start_date + timedelta(days=int(days))

    manager.run_schedule_optimization(time_limit)
    for event in manager.schedule():
        if well := wells[event.well]:
            ready_date = date(days=event.end)
            well.readydate = ready_date
            well.completion_date = date(days=event.completion)
            well.operations = (
                Operation.model_validate({"opname": "open", "date": ready_date}),
            )
