from collections import defaultdict
from typing import DefaultDict, Dict, Iterator, Optional, Sequence, Set, Tuple


class StateProcessor:
    def __init__(
        self,
        default: str,
        is_allow_action: bool,
        latest: Dict[str, str],
        actions: Optional[Sequence[Tuple[str, str]]] = None,
    ) -> None:
        """
        Initialize an instance of StateProcessor.

        Parameters:
        - default (str): The default state for the wells.
        - is_allow_action (bool): action context indicator (allow or refuse).
        - latest (Dict[str, str]): A dictionary mapping well names to their latest state.
        - actions (Optional[Sequence[Tuple[str, str]]]): actions to perform depending on context.

        Returns:
        - None
        """
        self.is_allow_action = is_allow_action
        self.latest = self._inverted_latest(latest)
        self.actions = actions
        self.default = default

    def _inverted_latest(self, states: Dict[str, str]) -> DefaultDict[str, Set[str]]:
        latest = defaultdict(set)
        for well, state in states.items():
            latest[state].add(well)
        return latest

    def _revert_latest(self) -> Iterator[Tuple[str, str]]:
        return ((well, state) for state, wells in self.latest.items() for well in wells)

    def _toggle_well_state(self, well: str, new: str, previous: str) -> None:
        if well not in self.latest[new]:
            self.latest[new].add(well)
            self.latest[previous].remove(well)

    # TODO: Use n_switch_states, actions and is is_allow_action
    # TODO: Make functions more generic (remove open and shut)
    def process(
        self, wells: Tuple[str, ...], n_max_wells: int, n_switch_states: int
    ) -> Iterator[Tuple[str, str]]:
        """
        Process the given priorities to toggle the state of wells

        Parameters:
        wells (Tuple[str, ...]): well order [highest,..., lowest] priority
        n_max_wells (int): The maximum number of wells to process.
        n_switch_states (int): The number of state switches allowed.

        Returns:
        Iterator[Tuple[str, str]]:  (well, state), ...

        Raises:
        ValueError: If n_max_wells is greater than the length of priorities.
        """

        if n_max_wells > len(wells):
            raise ValueError(
                "n_max_wells cannot be greater than the length of priorities"
            )

        for well in wells[:n_max_wells]:
            self._toggle_well_state(well, "open", "shut")
        for well in wells[n_max_wells:]:
            self._toggle_well_state(well, "shut", "open")

        return self._revert_latest()
