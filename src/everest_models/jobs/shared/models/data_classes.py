from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Dict, Iterator, Optional, Tuple

from .operation import Tokens


@dataclass
class Operation:
    date: date
    tokens: Tokens
    template: Optional[Path] = None


@dataclass
class Well:
    operations: Dict[str, Operation]
    readydate: Optional[date] = None
    completion_date: Optional[date] = None
    drill_time: Optional[int] = None

    @property
    def missing_templates(self) -> Iterator[Tuple[str, date]]:
        return (
            (operation_name, operation.date)
            for operation_name, operation in self.operations.items()
            if operation.template is None
        )
