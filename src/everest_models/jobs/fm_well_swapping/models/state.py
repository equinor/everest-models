from collections.abc import Collection, Sequence
from functools import cached_property
from logging import getLogger
from typing import (
    Any,
    Dict,
    Iterable,
    Iterator,
    List,
    Literal,
    NamedTuple,
    Set,
    Tuple,
    Union,
)

from pydantic import AfterValidator, Field, model_validator
from typing_extensions import Annotated, Final, Self, TypeAlias

from everest_models.jobs.shared.models import ModelConfig
from everest_models.jobs.shared.validators import min_length

SINGLE_WORD: Final = r"^[a-zA-Z][_\-a-zA-Z0-9]*$"
FILLER: Final = "_"
State: TypeAlias = str
Case: TypeAlias = str
Quota: TypeAlias = int
logger = getLogger("Well Swapping")


def unique_values(values: Sequence) -> Sequence:
    if len(set(values)) != len(values):
        raise ValueError("Values are not unique")
    return values


def _states_are_viable(states: Any, hierarchy: Tuple[State, ...]) -> None:
    if isinstance(states, str):
        if states == FILLER:
            return
        states = {states}

    if isinstance(states, dict):
        states = {state for state in states.values() if state != FILLER}
    elif isinstance(states, Sequence):
        states = {state for state in states if state != FILLER}

    if difference := ", ".join(states.difference(hierarchy)):
        raise ValueError(f"State not in hierarchy: {difference}")


def _all_states_accounted(
    values: Set[State], hierarchy: Set[State], field: str
) -> None:
    if difference := ", ".join(values - hierarchy):
        raise ValueError(
            f"Sates: {difference} found in `{field}` but not present in hierarchy"
        )


def _field_states_accounted(
    value: Collection, hierarchy: Set[State], field: str
) -> None:
    if isinstance(value, str) and value not in hierarchy:
        raise ValueError(f"{field} state {value} not in hierarchy")
    elif type(value) in (dict, Sequence):
        _all_states_accounted(
            set(value.values() if isinstance(value, dict) else value), hierarchy, field
        )


class Action(NamedTuple):
    source: State
    target: State


class StateHierarchy(ModelConfig):
    label: Annotated[str, Field(pattern=SINGLE_WORD, description="State's label/name.")]
    quotas: Annotated[
        Union[Quota, Tuple[Union[Quota, Literal["_"]], ...]],
        Field(
            default=None,
            description=(
                "Case state toggle quota per iteration.\n"
                "Tip: '_', (infinity) alias can be used to pad array\n"
                "Thus, if you wish all iteration to infinity, then omit this field\n"
                "Note: If a integer is given, all iterations will be that string"
            ),
            examples=[f"[{FILLER}, 4, {FILLER}, 2]", 2],
        ),
    ]

    def get_quotas(self, iterations: int, cases: int) -> List[Quota]:
        if self.quotas is None:
            return [cases] * iterations
        if isinstance(self.quotas, int):
            if self.quotas > cases:
                logger.warn(
                    "Quotas is greater than the available cases, "
                    f"quatas is set to {cases}, the total amount of cases."
                )
            return [self.quotas if self.quotas < cases else cases] * iterations
        quotas = [cases if quota == "_" else quota for quota in self.quotas]
        if len(self.quotas) < iterations:
            quotas += [cases] * (iterations - len(self.quotas))
        return quotas[:iterations] if iterations < len(quotas) else quotas

    def __hash__(self) -> int:
        return hash(self.label)

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, self.__class__) and other.label == self.label


class StateConfig(ModelConfig):
    hierarchy: Annotated[
        Tuple[StateHierarchy, ...],
        AfterValidator(unique_values),
        Field(
            min_length=2,
            description=(
                "State hierarchy in decending order [highest, ..., lowest]\n"
                "Note: values must be unique!\n"
                "Tip: highest is the default target state\n"
                "and lowest is the default initial state"
            ),
        ),
    ]
    initial: Annotated[
        Union[Dict[Case, State], State],
        AfterValidator(min_length(1)),
        Field(
            default=None,
            description=(
                "States to set cases to at initial iteration.\n"
                "Tip: fill only cases that differ from default "
                "(lowest priority level in hierarchy),\n"
                "since those are automatically populated for you.\n"
                "Thus, if you wish to initialize all values to default, "
                "then omit this field\n"
                "Note: If a string is given, all cases will be initialize to that string"
            ),
        ),
    ]
    targets: Annotated[
        Union[Tuple[Union[State, Literal["_"]], ...], State],
        AfterValidator(min_length(1)),
        Field(
            default=None,
            description=(
                "Target States for each iteration.\n"
                "Tip: '_', default alias can be used to pad array"
                "(highest priority level in hierarchy),\n"
                "since those are automatically populated for you.\n"
                "Thus, if you wish to initialize all values to default, "
                "then omit this field\n"
                "Note: If a string is given, all iterations will be initialize to that "
                "string"
            ),
            examples=[f"{FILLER}, sitting, {FILLER}, standing]", "sitting"],
        ),
    ]
    actions: Annotated[
        Tuple[Action, ...],
        AfterValidator(unique_values),
        Field(
            default=None,
            min_length=1,
            description=(
                "List of directional (source → target) state actions.\n"
                "Note: action context is set with the 'forbiden_actions' field"
            ),
        ),
    ]
    allow_inactions: Annotated[
        bool,
        Field(
            default=True,
            description=(
                "Are cases allowed to stay at the same state?\n"
                "False: Enforce cases to change state each iteration, (can cause state lock)\n"
                "True: Cases are allowed to stay at same state between iterations\n"
            ),
        ),
    ]
    forbiden_actions: Annotated[
        bool,
        Field(
            default=False,
            description=(
                "False: 'actions' is used as the only allowed state trasitions.\n"
                "True: 'actions' is negated from allowed state trasitions.\n"
                "Note: if 'actions' is not given this value is ignored"
            ),
        ),
    ]

    @model_validator(mode="before")  # type: ignore
    def set_empty_values(self) -> Dict[str, Any]:
        assert isinstance(self, dict)  # this is done for typechecker
        hierarchy = self.get("hierarchy", [{"label": None}])
        if self.get("initial") is None:
            self["initial"] = hierarchy[-1]["label"]
        if self.get("targets") is None:
            self["targets"] = hierarchy[0]["label"]
        return self

    @model_validator(mode="after")
    def initial_states_are_viable(self) -> Self:
        _states_are_viable(self.initial or self.lowest_priority, self.state_hierarchy)
        _states_are_viable(self.targets or self.highest_priority, self.state_hierarchy)
        return self

    @model_validator(mode="after")
    def all_states_accounted(self) -> Self:
        hierarchy = set(self.state_hierarchy)
        _field_states_accounted(self.initial, hierarchy, "initial")
        _field_states_accounted(self.targets, hierarchy, "targets")
        _all_states_accounted(
            {state for action in self.actions or () for state in action},
            hierarchy,
            "actions",
        )
        return self

    def get_initial(self, cases: Iterable[Case]) -> Dict[Case, State]:
        default = self.lowest_priority
        if self.initial is None:
            return {case: default for case in cases}
        if isinstance(self.initial, str):
            return {case: self.initial for case in cases}
        if cases == set(self.initial):
            return self.initial

        return {**{case: default for case in cases}, **self.initial}

    def get_targets(self, iterations: int) -> Tuple[State, ...]:
        default = self.highest_priority
        if self.targets is None:
            return (default,) * iterations
        if isinstance(self.targets, str):
            return (self.targets,) * iterations
        targets = [default if target == "_" else target for target in self.targets]
        if len(self.targets) < iterations:
            targets += [default] * (iterations - len(self.targets))
        return tuple(targets[:iterations] if iterations < len(targets) else targets)

    def get_quotas(self, iterations: int, cases: int) -> Iterator[Dict[State, Quota]]:
        return (
            dict(zip((item.label for item in self.hierarchy), value))
            for value in zip(
                *[item.get_quotas(iterations, cases) for item in self.hierarchy]
            )
        )

    @cached_property
    def state_hierarchy(self) -> Tuple[State, ...]:
        return tuple(item.label for item in self.hierarchy)

    @property
    def highest_priority(self) -> State:
        return self.state_hierarchy[0]

    @property
    def lowest_priority(self) -> State:
        return self.state_hierarchy[-1]
