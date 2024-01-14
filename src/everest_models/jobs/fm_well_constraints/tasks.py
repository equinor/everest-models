import datetime
import logging
from typing import Dict, List, NamedTuple, TypedDict

from everest_models.jobs.shared.models.wells import Operation

from .models import WellConstraints
from .models.config import Constraints

logger = logging.getLogger(__name__)


class _RatePhase(TypedDict):
    rate: Dict[int, float]
    phase: Dict[int, float]


class _Constraints(NamedTuple):
    rate_phase: _RatePhase
    duration: Dict[int, float]


def constraint_by_well_name(
    constraints: WellConstraints, well_name: str
) -> _Constraints:
    return _Constraints(
        duration=(constraints.get("duration") or {}).get(well_name) or {},
        rate_phase={
            "rate": (constraints.get("rate") or {}).get(well_name) or {},
            "phase": (constraints.get("phase") or {}).get(well_name) or {},
        },
    )


def create_well_operations(
    events: Dict[int, Constraints],
    start_date: datetime.date,
    constraints: _Constraints,
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
        operations.append(
            Operation(  # type: ignore
                tokens={
                    constraint_type: constraint.optimum_value(
                        constraints.rate_phase[constraint_type].get(index)
                    )
                    for constraint_type, constraint in event
                    if constraint_type != "duration"
                },
                opname="rate",
                date=start_date,
            )
        )
        start_date += datetime.timedelta(
            days=event.duration.optimum_value(constraints.duration.get(index))
        )

    return operations
