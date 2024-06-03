from typing import Iterable, List, Tuple

import numpy as np
import pandas as pd
from typing_extensions import Self, TypeAlias

from .models import State, StateConfig

Action: TypeAlias = Tuple[State, State]


def _build_state_matrix(
    states: List[State], actions: Iterable[Action], forbiden: bool, inaction: bool
) -> pd.DataFrame:
    size = len(states)
    data = (np.ones if forbiden or not actions else np.zeros)((size, size), dtype=int)
    np.fill_diagonal(data, 1 if inaction else 0)
    df = pd.DataFrame(data=data, index=states, columns=states)
    for source, target in actions:
        df.loc[source, target] = 0 if forbiden else 1
    return df


class StateMachine:
    """A state to state, action matrix wrapper."""

    def __init__(
        self,
        states: List[State],
        actions: Iterable[Action],
        forbiden: bool,
        inaction: bool,
    ) -> None:
        "Create an encapsulated action matrix."
        self.__matrix: pd.DataFrame = _build_state_matrix(
            states, actions, forbiden, inaction
        )

    @classmethod
    def from_config(cls, config: StateConfig) -> Self:
        """Build a state machine based on the user provided state configuration.

        This function only cares for:
            - hierarchy
            - actions
            - forbiden_actions

        Args:
            config (StateConfig): Validated state configuration values.

        Returns:
            StateMachine instance.
        """
        return cls(
            [item.label for item in config.hierarchy],
            config.actions or (),
            config.forbiden_actions,
            config.allow_inactions,
        )

    def is_possible_action(self, source: State, target: State) -> bool:
        """
        Check if a transition from source state to target state is possible.

        Args:
            source (str): The source state.
            target (str): The target state.

        Returns:
            True if transition is possible, False otherwise.
        """
        try:
            return bool(self.__matrix.loc[source, target])
        except KeyError:
            return False

    def next_possible_action(self, source: State, target: State) -> Action:
        """
        Find the next possible action from source state to target state.

        Args:
            source (str): The source state.
            target (str): The target state.

        Returns:
            The next possible action from source to target state.
        """
        row = self.__matrix.loc[source]
        index = self.__matrix.columns.get_loc(target) - 1 % len(self.__matrix.columns)  # type: ignore
        while True:
            if row.iloc[index] == 1:
                return (source, str(self.__matrix.columns[index]))
            index -= 1

    def __str__(self) -> str:
        return str(self.__matrix)
