from datetime import date, timedelta
from pathlib import Path
from typing import Dict, List, Literal, NamedTuple, Optional, Tuple, TypedDict

import pytest
from everest_models.jobs.fm_well_swapping.models import ConfigSchema
from everest_models.jobs.fm_well_swapping.tasks import (
    Data,
    clean_parsed_data,
    determine_index_states,
    duration_to_dates,
)
from everest_models.jobs.shared.models import Wells


class Constraints(TypedDict):
    state_duration: Tuple[float, ...]


class Options(NamedTuple):
    command: Literal["lint", "run"]
    config: ConfigSchema
    cases: Optional[Wells] = None
    priorities: Optional[List[Dict[str, float]]] = None
    constraints: Optional[Constraints] = None
    output: Optional[Path] = None
    iteration_limit: int = 0


minimum_data = {
    "constraints": {
        "state_duration": {"scaling": {"source": [0, 1], "target": [0, 500]}}
    },
    "start_date": "2024-06-03",
    "state": {"hierarchy": [{"label": "open"}, {"label": "shut"}]},
}
cases = Wells.model_validate([{"name": "W1"}, {"name": "W2"}, {"name": "W3"}])
data = Data(
    lint_only=True,
    iterations=2,
    priorities=(("W3", "W1", "W2"), ("W2", "W3", "W1")),
    quotas={"open": [3, 3], "shut": [3, 3]},
    initial_states={"W1": "shut", "W2": "shut", "W3": "shut"},
    cases=cases,
    output=None,  # type: ignore
    targets=("open", "open"),
    state_duration=(250, 250),
    errors=[],
)


# NOTE: There is way to many permutations.
# Please add the next edge case if one is found
@pytest.mark.parametrize(
    "options, expected",
    [
        pytest.param(
            Options(command="lint", config=ConfigSchema.model_validate(minimum_data)),
            Data(
                lint_only=True,
                iterations=0,
                priorities=(),
                quotas={"open": [], "shut": []},
                initial_states={},
                cases=None,  # type: ignore
                output=None,  # type: ignore
                targets=(),
                state_duration=None,  # type: ignore
                errors=[
                    "no priorities",
                    "no initial states",
                    "no cases",
                    "Iteration must be greater than zero.",
                    "no targets",
                    "no state duration",
                ],
            ),
            id="minimum",
        ),
        pytest.param(
            Options(
                command="lint",
                config=ConfigSchema.model_validate(minimum_data),
                cases=cases,
                priorities=[
                    {"W1": 0.51, "W2": 0.40, "W3": 0.55},
                    {"W1": 0.50, "W2": 0.54, "W3": 0.51},
                ],
                constraints={"state_duration": (0.5, 0.5)},
            ),
            data,
            id="all files present",
        ),
        pytest.param(
            Options(
                command="lint",
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
            data,
            id="config backups",
        ),
        pytest.param(
            Options(
                command="lint",
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
            data,
            id="files have priority over fallback",
        ),
    ],
)
def test_clean_parsed_data(options: Options, expected: Data):
    data = clean_parsed_data(options)  # type: ignore
    assert isinstance(data, Data)
    assert data.lint_only == expected.lint_only
    assert data.iterations == expected.iterations
    assert data.priorities == expected.priorities
    assert data.quotas == expected.quotas
    assert data.initial_states == expected.initial_states
    assert data.cases == expected.cases
    assert data.output == expected.output
    assert data.targets == expected.targets
    assert data.state_duration == expected.state_duration
    assert data.errors == expected.errors


# Test duration_to_dates function
def test_duration_to_dates():
    start_date = date(2024, 1, 1)
    assert list(duration_to_dates([1, 2, 3], start_date)) == [
        start_date,
        start_date + timedelta(days=1),
        start_date + timedelta(days=3),
        start_date + timedelta(days=6),
    ]


# None positive numbers are never tested, but those test cases would never happen
@pytest.mark.parametrize(
    "iterations, expected",
    (
        pytest.param(
            1, ([("case1", "state1"), ("case2", "state1")],), id="one iterations"
        ),
        pytest.param(
            2,
            (
                [("case1", "state1"), ("case2", "state1")],
                [("case3", "state2"), ("case4", "state2")],
            ),
            id="max iterations",
        ),
        pytest.param(
            3,
            (
                [("case1", "state1"), ("case2", "state1")],
                [("case3", "state2"), ("case4", "state2")],
            ),
            id="surpass max",
        ),
    ),
)
def test_determine_index_states(
    iterations: int, expected: Tuple[Tuple[Tuple[str, str], ...], ...]
):
    class MockStateProcessor:
        def process(self, cases, target, _):
            return [(case, target) for case in cases]

    assert (
        tuple(
            determine_index_states(
                process_params=[
                    (("case1", "case2"), "state1"),
                    (("case3", "case4"), "state2"),
                ],
                state_processor=MockStateProcessor(),  # type: ignore
                iterations=iterations,
            )
        )
        == expected
    )
