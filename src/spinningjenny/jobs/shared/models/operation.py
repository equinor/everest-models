import datetime
import sys
from typing import Any, Dict, Iterable, Optional, Tuple, TypeVar

from pydantic import Extra, Field, FilePath, root_validator

from spinningjenny.jobs.shared.models.base_config import BaseConfig
from spinningjenny.jobs.shared.models.phase import PhaseEnum
from spinningjenny.jobs.shared.validators import validate_no_extra_fields

if sys.version_info.minor < 9:
    from typing_extensions import TypedDict
else:
    from typing import TypedDict


class Tokens(TypedDict, total=False):
    phase: PhaseEnum
    rate: float

    @classmethod
    def value_type(cls) -> Dict[str, Any]:
        return {
            "phase": PhaseEnum.value_type(),
            "rate": "float",
            "<string>": "<any value>",
        }


class _Operation(BaseConfig):
    date: datetime.date
    opname: str
    template: Optional[FilePath] = None


class Operation(_Operation, extra=Extra.allow):
    tokens: Tokens = Field(default_factory=dict)

    @root_validator(pre=True)
    def no_extra_based_fields(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        validate_no_extra_fields(
            "date", "opname", "template", "tokens", values=iter(values)
        )
        return values


class LegacyOperation(_Operation):
    phase: Optional[PhaseEnum] = None
    rate: Optional[float] = None


OperationType = TypeVar("OperationType", Operation, LegacyOperation)


def update_legacy_operations(
    operations: Iterable[OperationType],
) -> Tuple[Operation, ...]:
    def update(operation: OperationType) -> Operation:
        if isinstance(operation, Operation):
            return operation
        keys = {"phase", "rate"}
        op = operation.dict(exclude=keys, exclude_none=True, exclude_unset=True)
        return Operation(
            tokens={
                key: value
                for key in keys
                if (value := getattr(operation, key, None)) is not None
            },
            **op,
        )

    return tuple(update(operation) for operation in operations)
