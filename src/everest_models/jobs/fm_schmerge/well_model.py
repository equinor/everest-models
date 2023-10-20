from collections import defaultdict
from typing import Tuple, TypeVar

from pydantic import FilePath

from everest_models.jobs.shared.models import Operation, Well, WellConfig
from everest_models.jobs.shared.models.operation import LegacyOperation


class _Operation(Operation):
    template: FilePath


class _LegacyOperation(LegacyOperation):
    template: FilePath


OperationType = TypeVar("OperationType", _Operation, _LegacyOperation)


class Well(Well):
    ops: Tuple[OperationType, ...]


class Wells(WellConfig):
    __root__: Tuple[Well, ...]

    def dated_operations(self):
        operations_dict = defaultdict(list)
        for well in self:
            for operation in well.ops:
                operations_dict[operation.date].append(
                    {
                        "template_map": dict(
                            filter(
                                lambda x: x[1] is not None,
                                {"name": well.name, **operation.tokens}.items(),
                            )
                        ),
                        "template": operation.template,
                    }
                )
        return operations_dict
