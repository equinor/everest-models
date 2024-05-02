from datetime import date
from functools import cached_property
from pathlib import Path
from textwrap import dedent
from typing import Dict, List, NamedTuple, Optional, Sequence, Set, Tuple

from pydantic import (
    Field,
    FilePath,
    ValidationInfo,
    field_validator,
    model_validator,
)
from typing_extensions import Annotated, Self

from everest_models.jobs.shared import rescale_value
from everest_models.jobs.shared.models import ModelConfig, Wells
from everest_models.jobs.shared.validators import parse_file

SINGLE_WORD = r"^[a-zA-Z][_\-a-zA-Z0-9]*$"


def file_path_description(argument: str) -> str:
    message = f"Everest generated well {argument}"
    if argument == "wells":
        message = "Everest generated or forward model modified wells json file"
    if argument == "output":
        message = "where you wish to output the modified wells json file"
    return dedent(
        f"""
        Relative or absolute path to {message}.
        NOTE: --{argument.lower()} {argument.upper()} argument overrides this field
        """
    )


def validate_priorities_and_state_initial_same_wells(
    priority_wells: Set[str], initial_wells: Set[str]
) -> None:
    if (
        priority_wells
        and initial_wells
        and (difference := ", ".join(priority_wells ^ initial_wells))
    ):
        raise ValueError(
            f"There are some discrepancies in `properties` and/or `initial_states`: {difference}"
        )


class Priorities(ModelConfig):
    file_path: Annotated[
        FilePath, Field(None, description=file_path_description("priorities"))
    ]
    fallback_values: Annotated[
        Dict[str, List[float]],
        Field(
            default=None,
            description="fallback priorities if priorities file is not given",
        ),
    ]

    @property
    def wells(self) -> Tuple[str, ...]:
        return tuple(self.fallback_values) if self.fallback_values else ()

    @cached_property
    def inverted(self) -> List[Dict[str, float]]:
        if not (priorities := self.fallback_values):
            return []

        return [
            {well: priorities[well][index] for well in priorities}
            for index in range(len(next(iter(priorities.values()))))
        ]


class Bound(NamedTuple):
    min: float
    max: float


class Scaling(ModelConfig):
    source: Annotated[
        Bound,
        Field(description="[min, max] values for scaling source"),
    ]
    target: Annotated[
        Bound,
        Field(description="[min, max] values for scaling target"),
    ]

    @field_validator("*", mode="after")
    def valid_bound(cls, bound: Bound) -> Bound:
        if bound.min > bound.max:
            raise ValueError(
                f"[min, max], where min cannot be greater than max: {list(bound)}"
            )
        return bound


class _Constraint(ModelConfig):
    fallback_values: Annotated[
        List[int],
        Field(
            default=None,
            description="A list of values to fallback on if constraint json file is not present",
        ),
    ]
    scaling: Annotated[
        Scaling,
        Field(
            description="Scaling data used by everest for producing constraint files, "
            "given these values this well swapping forward model will rescale the constraints"
        ),
    ]


class Constraints(ModelConfig):
    file_path: Annotated[
        FilePath,
        Field(None, description=file_path_description("constraints")),
    ]
    n_max_wells: Annotated[
        _Constraint,
        Field(description="Constraint information for maximum number of wells"),
    ]
    n_switch_states: Annotated[
        _Constraint,
        Field(description="Constraint information for number state switches allowed"),
    ]
    state_duration: Annotated[
        _Constraint,
        Field(
            description="Constraint information for the time duration of any given state"
        ),
    ]

    @model_validator(mode="after")
    def same_fallback_length(self) -> Self:
        if (
            len(
                set(
                    fallbacks := {
                        field: len(values)
                        for field in (
                            "n_max_wells",
                            "n_switch_states",
                            "state_duration",
                        )
                        if (values := getattr(self, field).fallback_values)
                    }.values()
                )
            )
            > 1
        ):
            raise ValueError(f"Fallback values are not the same length: {fallbacks}")
        return self

    def rescale(
        self, constraints: Optional[Dict[str, Sequence[float]]]
    ) -> Dict[str, Tuple[int, ...]]:
        """
        Rescale the constraints based on the scaling parameters of the fields.
        Each constraint is rescaled and rounded to an integer

        Parameters:
        - constraints (Dict[str, Sequence[float]]): A dictionary where keys are one of the following n_max_wells and/or n_switch_states and state_duration and values are sequences of float to be rescaled.

        Returns:
        - Dict[str, Tuple[int, ...]]: A dictionary where keys are field names and values are tuples of rescaled integer values.

        Example:
        constraints = {'field1': [0.5, 0.75, 1.0], 'field2': [10.0, 15.0, 20.0]}
        rescaled_constraints = rescale_constraints(constraints)
        # Output: {'field1': (1, 2, 3), 'field2': (10, 15, 20)}
        """

        if not constraints:
            return {
                field: tuple(values)
                for field in ("n_max_wells", "n_switch_states", "state_duration")
                if (values := getattr(self, field).fallback_values)
            }

        def rescale(field: str, values: Sequence[float]) -> Tuple[int, ...]:
            scaling = getattr(self, field).scaling
            return tuple(
                round(
                    rescale_value(
                        value,
                        scaling.source.min,
                        scaling.source.max,
                        scaling.target.min,
                        scaling.target.max,
                    )
                )
                for value in values
            )

        return {
            constraint: rescale(constraint, values)
            for constraint, values in constraints.items()
        }


class DircetionalState(ModelConfig):
    source: Annotated[str, Field(pattern=SINGLE_WORD)]
    target: Annotated[str, Field(pattern=SINGLE_WORD)]

    @model_validator(mode="after")
    def different_source_target_value(self) -> Self:
        if self.source == self.target:
            raise ValueError("source and values cannot be the same")
        return self


class State(ModelConfig):
    viable: Annotated[
        Tuple[str, ...],
        Field(
            min_length=2,
            description=(
                "viable well operation states.\n"
                "Note: order matters, if 'initial' is not given, "
                "then one will be created using 'priorities' and first value.\n"
            ),
        ),
    ]
    initial: Annotated[
        Dict[str, str],
        Field(
            default=None,
            min_length=1,
            description=(
                "States to set wells to at initial iteration.\n"
                "Tip: fill only wells that differ from default (first element of 'viable'), "
                "since those are automatically populated for you"
            ),
        ),
    ]
    actions: Annotated[
        List[DircetionalState],
        Field(
            default=None,
            min_length=1,
            description=(
                "List of allowed or prohibited directional (source → target) state actions.\n"
                "Note: allowed or prohibited context is set with the 'is_allowed_action' field"
            ),
        ),
    ]
    is_allow_action: Annotated[
        bool,
        Field(
            default=True,
            description=(
                "True: 'actions' field are taken as allowed state actions.\n"
                "False: 'actions' field are taken as prohibited state actions.\n"
                "Note: if 'actions' is not given this value is ignored"
            ),
        ),
    ]

    @field_validator("initial")
    def initial_states_are_viable(
        cls, initial: Dict[str, str], info: ValidationInfo
    ) -> Dict[str, str]:
        if initial and (
            difference := ", ".join(
                set(initial.values()).difference(info.data["viable"])
            )
        ):
            raise ValueError(f"Non-viable status given: {difference}")
        return initial

    @property
    def wells(self) -> Tuple[str, ...]:
        return tuple(self.initial) if self.initial else ()


class ConfigSchema(ModelConfig):
    priorities: Priorities
    constraints: Annotated[
        Constraints,
        Field(
            description=dedent(
                """
                Make sure the following are present in you Everest configuration file.

                create a generic control where the control variables are:
                'n_max_wells', 'n_switch_states', and 'state_duration'
                and the length of all initial_guesses are n+1,
                where 'n' is the nth index in the initial_guess array

                controls:
                - name: <name of constraint file>
                    type: generic_control
                    variables:
                    - { name: n_max_wells, initial_guess: [x0, x1, ..., xn] }
                    - { name: n_switch_states, initial_guess: [y0, y1, ..., yn ] }
                    - { name: state_duration, initial_guess: [z0, z1, ..., zn] }
            """
            )
        ),
    ]
    start_date: date
    state: State
    output: Annotated[Path, Field(None, description=file_path_description("output"))]
    wells: Annotated[Path, Field(None, description=file_path_description("wells"))]

    def wells_instance(self) -> Optional[Wells]:
        if not self.wells:
            return
        return parse_file(str(self.wells), Wells)

    def initial_states(self, wells: Optional[Sequence[str]]) -> Dict[str, str]:
        """
        Generate initial states for the given wells.

        Args:
            wells (Optional[Sequence[str]]): A sequence of well names for which initial states need to be generated.
                If None, initial states will be generated for using 'priorities' and first value of 'state.viable'.

        Returns:
            Dict[str, str]: A dictionary mapping well names to their initial states.

        Raises:
            ValueError: If no wells are provided and there are no priorities to generate initial states.

        Example:
            > initial_states(['A', 'B', 'C'])
            {'A': 'initial_state_A', 'B': 'initial_state_B', 'C': 'initial_state_C'}
        """
        initial = self.state.initial
        if not (wells := wells or self.priorities.wells or self.state.wells):
            raise ValueError("No wells to generate initial states")
        if initial and tuple(initial) == wells:
            return initial
        _initial = {well: self.state.viable[0] for well in wells}
        return _initial if not initial else {**_initial, **initial}
