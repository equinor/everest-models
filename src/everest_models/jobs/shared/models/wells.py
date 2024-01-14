from datetime import date
from pathlib import Path
from typing import Dict, Iterator, Tuple

from pydantic import ConfigDict, Field
from typing_extensions import Annotated

from .base_config import ModelConfig, RootModelConfig
from .operation import Operation

OPERATIONS_FIELD_ATTRIBUTE = {
    "default_factory": tuple,
    "description": "Sequence of operations",
    "alias": "ops",
}


class Well(ModelConfig):
    model_config = ConfigDict(frozen=False)

    completion_date: Annotated[date, Field(None, description="")]
    drill_time: Annotated[int, Field(None, description="")]
    name: Annotated[str, Field(frozen=True, description="Well name")]
    operations: Annotated[Tuple[Operation, ...], Field(**OPERATIONS_FIELD_ATTRIBUTE)]
    readydate: Annotated[date, Field(None, description="")]

    def __hash__(self):
        return hash(self.name)

    @property
    def missing_templates(self) -> Iterator[Tuple[str, date]]:
        return (
            (operation.opname, operation.date)
            for operation in self.operations
            if operation.template is None
        )


class Wells(RootModelConfig):
    root: Tuple[Well, ...]

    model_config = ConfigDict(frozen=False)

    def __iter__(self) -> Iterator[Well]:  # type: ignore
        return iter(self.root)

    def __getitem__(self, item: int):
        return self.root[item]

    def to_dict(self) -> Dict[str, Well]:
        return {well.name: well for well in self}

    def json_dump(self, output: Path) -> None:
        """Write instance state to a JSON file.

        Args:
            output (pathlib.Path): file to write to
        """
        output.write_text(
            self.model_dump_json(
                indent=2,
                exclude_none=True,
                exclude_unset=True,
                by_alias=True,
            )
        )
