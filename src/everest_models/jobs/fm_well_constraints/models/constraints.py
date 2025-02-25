from typing import Dict, Iterator, Optional, TypedDict, overload

from pydantic import field_validator

from everest_models.jobs.shared.models import RootModelConfig


class Control(RootModelConfig):
    """An 'immutable' well control optimizer value schema.

    The schema is a container for a two layers deep dictionary.
    First layer key is a string that represents the well name.
    Second layer key is an integer that represent the optimizer_value index
    """

    root: Dict[str, Dict[int, float]]

    def __iter__(self) -> Iterator[str]:  # type: ignore
        return iter(self.root)

    @overload
    def get(self, __key: str) -> Dict[int, float]: ...

    @overload
    def get(self, __key: str, __default: Dict[int, float]) -> Dict[int, float]: ...

    def get(
        self, __key: str, __default: Optional[Dict[int, float]] = None
    ) -> Optional[Dict[int, float]]:
        if __default is None:
            return self.root.get(__key)
        return self.root.get(__key, __default)


class PhaseControl(Control):
    @field_validator("root")
    @classmethod
    def is_within_bounds(cls, root):
        assert not (
            error := [
                f"{name} -> {index} -> {value}"
                for name, constraint in root.items()
                for index, value in constraint.items()
                if not 0 <= value <= 1
            ]
        ), "Value(s) are not within bounds [0, 1]:\n\t" + "\t".join(error)
        return root


class WellConstraints(TypedDict):
    duration: Control
    rate: Control
    phase: PhaseControl
