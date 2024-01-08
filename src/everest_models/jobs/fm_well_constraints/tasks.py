import datetime
import logging
from typing import Dict, List

from everest_models.jobs.fm_well_constraints.models import Constraints
from everest_models.jobs.fm_well_constraints.models.config import (
    Constraints as ConfigConstraints,
)
from everest_models.jobs.shared.models.wells import Operation

logger = logging.getLogger(__name__)


def create_well_operations(
    events: Dict[int, ConfigConstraints],
    well_name: str,
    start_date: datetime.date,
    constraints: Dict[str, Constraints],
) -> List[Operation]:
    """Create Well Operation based on the constraints

    Args:
        events (Dict[int, ConfigConstraints]): indexed well constraint configuration
        well_name (str): Well name
        start_date (datetime.date): start date
        constraints (Dict[str, Constraints]): well constraints

    Returns:
        List[Operation]: List of newly created well operation
    """
    operations = []
    for index, event in events.items():
        operation = Operation.model_validate(
            {
                "tokens": {
                    constraint_type: constraint.optimum_value(
                        constraints[constraint_type].get(well_name, {}).get(index)
                        if constraint_type in constraints
                        else None
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
