import datetime
import logging
from typing import NamedTuple, TypedDict

from everest_models.jobs.shared.models.wells import Operation

from .models import Control, WellConstraints
from .models.config import Constraints

logger = logging.getLogger(__name__)


class _RatePhase(TypedDict):
    rate: dict[int, float]
    phase: dict[int, float]


class _Constraints(NamedTuple):
    rate_phase: _RatePhase
    duration: dict[int, float]


def constraint_by_well_name(
    constraints: WellConstraints, well_name: str
) -> _Constraints:
    def well_values(control: Control | None) -> dict[int, float]:
        return (control.get(well_name) or {}) if control else {}

    return _Constraints(
        duration=well_values(constraints.get("duration")),
        rate_phase={
            "rate": well_values(constraints.get("rate")),
            "phase": well_values(constraints.get("phase")),
        },
    )


def create_well_operations(
    events: dict[int, Constraints],
    start_date: datetime.date,
    constraints: _Constraints,
) -> list[Operation]:
    """Create Well Operation based on the constraints

    Args:
        events (Dict[int, ConfigConstraints]): indexed well constraint configuration
        start_date (datetime.date): start date
        constraints (Dict[str, Constraints]): well constraints

    Returns:
        List[Operation]: List of newly created well operation
    """
    operations = []
    for index, event in events.items():
        operations.append(
            Operation(  # type: ignore[call-arg]
                tokens={  # type: ignore[arg-type]
                    constraint_type: constraint.optimum_value(
                        constraints.rate_phase[constraint_type].get(index)  # type: ignore[literal-required]
                    )
                    for constraint_type, constraint in event
                    if constraint_type != "duration"
                },
                opname="rate",
                date=start_date,
            )
        )
        duration = event.duration.optimum_value(constraints.duration.get(index))
        if duration is None:
            raise ValueError(
                f"Missing 'duration' value for well operation at index {index}; "
                "provide it in the configuration or the duration-constraint file."
            )
        start_date += datetime.timedelta(days=duration)

    return operations
