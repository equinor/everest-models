from datetime import date, timedelta
from pathlib import Path
from typing import Any, Dict, List, Literal, NamedTuple, Optional, Tuple, TypedDict

import pytest
from everest_models.jobs.fm_well_swapping.models import ConfigSchema
from everest_models.jobs.fm_well_swapping.tasks import (
    Data,
    clean_data,
    duration_to_dates,
    sorted_case_priorities,
)
from everest_models.jobs.shared.models import Wells


class Constraints(TypedDict):
    state_duration: Tuple[float, ...]


class Options(NamedTuple):
    config: ConfigSchema
    cases: Optional[Wells] = None
    priorities: Optional[List[Dict[str, float]]] = None
    constraints: Optional[Constraints] = None
    output: Optional[Path] = None
    command: Literal["lint", "run"] = "lint"
    iteration_limit: int = 0


minimum_data = {
    "constraints": {
        "state_duration": {"scaling": {"source": [0, 1], "target": [0, 500]}}
    },
    "start_date": "2024-06-03",
    "state": {"hierarchy": [{"label": "open"}, {"label": "shut"}]},
}
cases = Wells.model_validate([{"name": "W1"}, {"name": "W2"}, {"name": "W3"}])


def result(data: Dict[str, Any]) -> Data:
    return Data(
        lint_only=False,
        start_date=date(2024, 6, 3),
        iterations=2,
        priorities=(("W3", "W1", "W2"), ("W2", "W3", "W1")),
        state=ConfigSchema.model_validate(data),  # type: ignore
        cases=cases,
        output=None,  # type: ignore
        state_duration=(250, 250),
        errors=["no output"],
    )


# NOTE: There is way to many permutations.
# Please add the next edge case if one is found
@pytest.mark.parametrize(
    "options, expected",
    [
        pytest.param(
            Options(config=ConfigSchema.model_validate(minimum_data)),
            Data(
                lint_only=True,
                start_date=date(2024, 6, 3),
                iterations=0,
                priorities=(),
                state=ConfigSchema.model_validate(minimum_data),  # type: ignore
                cases=None,  # type: ignore
                output=None,  # type: ignore
                state_duration=None,  # type: ignore
                errors=[],
            ),
            id="minimum",
        ),
        pytest.param(
            Options(
                command="run",
                config=ConfigSchema.model_validate(minimum_data),
                cases=cases,
                priorities=[
                    {"W1": 0.51, "W2": 0.40, "W3": 0.55},
                    {"W1": 0.50, "W2": 0.54, "W3": 0.51},
                ],
                constraints={"state_duration": (0.5, 0.5)},
            ),
            result(minimum_data),
            id="all files present",
        ),
        pytest.param(
            Options(
                command="run",
                config=ConfigSchema.model_validate(
                    {
                        **minimum_data,
                        "priorities": {
                            "fallback_values": {
                                "W1": [0.51, 0.50],
                                "W2": [0.40, 0.54],
                                "W3": [0.55, 0.51],
                            }
                        },
                        "constraints": {
                            "state_duration": {
                                "fallback_values": 250,
                                **minimum_data["constraints"]["state_duration"],
                            }
                        },
                    }
                ),
                cases=cases,
            ),
            result(
                {
                    **minimum_data,
                    "priorities": {
                        "fallback_values": {
                            "W1": [0.51, 0.50],
                            "W2": [0.40, 0.54],
                            "W3": [0.55, 0.51],
                        }
                    },
                    "constraints": {
                        "state_duration": {
                            "fallback_values": 250,
                            **minimum_data["constraints"]["state_duration"],
                        }
                    },
                }
            ),
            id="config backups",
        ),
        pytest.param(
            Options(
                command="run",
                config=ConfigSchema.model_validate(
                    {
                        **minimum_data,
                        "priorities": {
                            "fallback_values": {
                                # flip W1 and W2
                                "W1": [0.40, 0.54],
                                "W2": [0.51, 0.50],
                                "W3": [0.55, 0.51],
                            }
                        },
                        "constraints": {
                            "state_duration": {
                                # make fallback bigger
                                "fallback_values": 300,
                                **minimum_data["constraints"]["state_duration"],
                            }
                        },
                    }
                ),
                cases=cases,
                priorities=[
                    {"W1": 0.51, "W2": 0.40, "W3": 0.55},
                    {"W1": 0.50, "W2": 0.54, "W3": 0.51},
                ],
                constraints={"state_duration": (0.5, 0.5)},
            ),
            result(
                {
                    **minimum_data,
                    "priorities": {
                        "fallback_values": {
                            # flip W1 and W2
                            "W1": [0.40, 0.54],
                            "W2": [0.51, 0.50],
                            "W3": [0.55, 0.51],
                        }
                    },
                    "constraints": {
                        "state_duration": {
                            # make fallback bigger
                            "fallback_values": 300,
                            **minimum_data["constraints"]["state_duration"],
                        }
                    },
                }
            ),
            id="files have priority over fallback",
        ),
    ],
)
def test_clean_parsed_data(options: Options, expected: Data):
    data = clean_data(options)  # type: ignore
    assert isinstance(data, Data)
    assert data.lint_only is expected.lint_only
    assert data.start_date == expected.start_date
    assert data.iterations == expected.iterations
    assert data.priorities == expected.priorities
    assert data.cases == expected.cases
    assert data.output == expected.output
    # assert data.states == expected.states
    assert data.state_duration == expected.state_duration
    assert data.errors == expected.errors


def test_duration_to_dates() -> None:
    start_date = date(2024, 1, 1)
    assert list(duration_to_dates([1, 2, 3], start_date)) == [
        start_date,
        start_date + timedelta(days=1),
        start_date + timedelta(days=3),
        start_date + timedelta(days=6),
    ]


@pytest.mark.parametrize(
    "value, expected",
    (
        pytest.param((), (), id="empty"),
        pytest.param(({"SINGLE": 0.9},), (("SINGLE",),), id="single value"),
        pytest.param(
            ({"W1": 0.51, "W2": 0.40, "W3": 0.55},),
            (("W3", "W1", "W2"),),
            id="multi value",
        ),
        pytest.param(
            (
                {"W1": 0.51, "W2": 0.40, "W3": 0.55},
                {"W1": 0.50, "W2": 0.54, "W3": 0.51},
            ),
            (("W3", "W1", "W2"), ("W2", "W3", "W1")),
            id="multi iteration",
        ),
    ),
)
def test_sorted_case_priorities(
    value: List[Dict[str, float]], expected: Tuple[Tuple[str, ...]]
) -> None:
    assert sorted_case_priorities(value) == expected


# need a propper way of test determine_index_states
