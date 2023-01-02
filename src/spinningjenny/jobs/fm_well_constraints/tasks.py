import datetime
import logging
from typing import Dict

from spinningjenny.jobs.fm_well_constraints.models import Constraints
from spinningjenny.jobs.fm_well_constraints.models.config import (
    Constraints as ConfigConstraints,
)
from spinningjenny.jobs.shared.models.wells import Operation

logger = logging.getLogger(__name__)


def create_well_operations(
    events: Dict[int, ConfigConstraints],
    well_name: str,
    start_date: datetime.date,
    constraints: Dict[str, Constraints],
):
    operations = []
    for index, event in events.items():
        operation = Operation.parse_obj(
            {
                **{
                    constraint_type: constraint.optimum_value(
                        constraints[constraint_type].get(well_name, {}).get(index)
                    )
                    for constraint_type, constraint in event
                    if constraint_type != "duration"
                },
                "opname": "rate",
                "date": start_date,
            }
        )
        operations.append(operation)
        start_date += datetime.timedelta(
            days=event.duration.optimum_value(
                constraints.get("duration", {}).get(well_name, {}).get(index)
            )
        )

    return operations
