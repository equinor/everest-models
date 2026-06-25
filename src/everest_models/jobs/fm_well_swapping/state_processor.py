from __future__ import annotations

from collections.abc import Iterable, Iterator
from logging import getLogger

from .models import Case, Quota, State, StateConfig
from .state_machine import StateMachine

logger = getLogger("Well Swapping")


class StateProcessor:
    @classmethod
    def from_state_config(
        cls, state: StateConfig, cases: tuple[Case, ...]
    ) -> StateProcessor:
        return cls(
            state_machine=StateMachine.from_config(state),
            initial_states=state.get_initial(cases),
        )

    def __init__(
        self, state_machine: StateMachine, initial_states: dict[Case, State]
    ) -> None:
        self._locked: bool = False
        self._machine: StateMachine = state_machine
        self._history: dict[Case, list[State]] = {
            subject: [state] for subject, state in initial_states.items()
        }

    @property
    def is_locked(self) -> bool:
        return self._locked

    def _recurse_state_hierarchy(
        self, quotas: dict[State, Quota], state: State, target: State
    ) -> State:
        if self._machine.is_possible_action(state, target) and quotas[target] > 0:
            return target
        return self._recurse_state_hierarchy(
            quotas, *self._machine.next_possible_action(state, target)
        )

    def _state_toggler(
        self, case: Case, target: State, quotas: dict[State, Quota]
    ) -> None:
        history = self._history[case]
        state = self._recurse_state_hierarchy(quotas, history[-1], target)
        quotas[state] -= 1
        history.append(state)

    def process(
        self, cases: Iterable[Case], target: State, quotas: dict[State, Quota]
    ) -> None:
        if not set(cases).issubset(self._history):
            raise ValueError("Case names must be a subset of initial state cases")
        for case in cases:
            try:
                self._state_toggler(case, target, quotas)
            except RecursionError:
                logger.warning(
                    "Encounter a state lock:\n"
                    f"{case = }\t"
                    f"source = {self._history[case][-1]}\t{target = }\n"
                    f"current state map:\n{self._machine}\n"
                    f"state tree history:\n{self._history}\n"
                    f"iteration quotas:\n{quotas}\n"
                )
                self._locked = True
                break

    def latest_valid_states(self, index: int) -> Iterator[tuple[Case, State]]:
        if not index and self._locked:
            raise RuntimeError(
                "A state lock was found on the first iteration.\n"
                f"current state map:\n{self._machine}\n"
                "Please check the states section in your configuration."
            )
        return (
            (case, states[index - 1 if self._locked else -1])
            for case, states in self._history.items()
        )
