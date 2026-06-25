from collections.abc import Iterator
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from .operation import Tokens


@dataclass
class Operation:
    date: date
    tokens: Tokens
    template: Path | None = None


@dataclass
class Well:
    operations: dict[str, Operation]
    readydate: date | None = None
    completion_date: date | None = None
    drill_time: int | None = None

    @property
    def missing_templates(self) -> Iterator[tuple[str, date]]:
        return (
            (operation_name, operation.date)
            for operation_name, operation in self.operations.items()
            if operation.template is None
        )
