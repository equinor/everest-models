from typing import Dict, Iterable, Iterator, List, Tuple

from .models import Case, Quota, State
from .state_machine import StateMachine


class StateProcessor:
    def __init__(
        self,
        state_machine: StateMachine,
        initial_states: Dict[Case, State],
        quotas: Dict[State, List[Quota]],
    ) -> None:
        """
        Create a StateProcessor instance.

        Parameters:
        state_machine (StateMachine): A pandas state matrix wrapper that implements `is_possible_action` and `next_possible_action`.
        initial_states (Dict[str, str]): A map of case to it's initial state.
        quotas (Dict[str, List[int]]): A map of state to it's quotas per iteration index.

        Returns:
        None
        """
        self._machine: StateMachine = state_machine
        self._history: Dict[Case, List[State]] = {
            subject: [state] for subject, state in initial_states.items()
        }
        self._quotas: Dict[State, List[Quota]] = quotas

    def _recurse_state_hierarcy(self, index: int, state: State, target: State) -> State:
        if (
            self._machine.is_possible_action(state, target)
            and self._quotas[target][index] > 0
        ):
            return target
        return self._recurse_state_hierarcy(
            index, *self._machine.next_possible_action(state, target)
        )

    def _state_toggler(self, case: Case, target: State, index: int) -> None:
        history = self._history[case]
        source = history[-1]
        state = self._recurse_state_hierarcy(index, source, target)
        self._quotas[state][index] -= 1
        history.append(state)

    def process(
        self, cases: Iterable[Case], target: State, index: int
    ) -> Iterator[Tuple[Case, State]]:
        """
        Process given cases to target state.

        If state target is not possible transition to the next possible state.

        Parameters:
        cases (Iterable[str]): The cases to be processed.
        target (str): The target state to transition to.
        index (int): The current iteration.

        Returns:
        Iterator[Tuple[str, str]]: An iterator yielding tuples of case and it's post-process state.
        """
        if not set(cases).issubset(self._history):
            raise ValueError("Case names must be a subset of initial state cases")
        for case in cases:
            self._state_toggler(case, target, index)
        return ((case, states[-1]) for case, states in self._history.items())
