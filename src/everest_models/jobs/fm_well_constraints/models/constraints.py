from typing import Dict

from pydantic import validator

from everest_models.jobs.shared.models import BaseFrozenConfig, DictRootMixin


class Constraints(BaseFrozenConfig, DictRootMixin):
    """An 'immutable' well constraint optimizer value schema.

    The schema is a container for a two layers deep dictionary.
    First layer key is a string that represents the well name.
    Second layer key is an integer that represent the optimizer_value index
    """

    __root__: Dict[str, Dict[int, float]]

    @validator("__root__")
    def is_within_bounds(cls, root):
        assert not (
            error := [
                f"{name} -> {index} -> {value}"
                for name, constraint in root.items()
                for index, value in constraint.items()
                if not 0 <= value <= 1
            ]
        ), f"Value(s) are not within bounds [0, 1]:\n\t" + "\t".join(error)
        return root
