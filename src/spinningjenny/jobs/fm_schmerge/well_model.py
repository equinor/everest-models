from collections import defaultdict
from typing import Tuple

from pydantic import FilePath

from spinningjenny.jobs.shared.models.wells import Operation, WellListModel, WellModel


class _Operation(Operation):
    template: FilePath


class Well(WellModel):
    ops: Tuple[_Operation, ...]


class Wells(WellListModel):
    __root__: Tuple[Well, ...]

    def dated_operations(self):
        operations_dict = defaultdict(list)
        for well in self:
            for operations in well.ops:
                operations_dict[operations.date].append(
                    {
                        **operations.dict(
                            include={"rate", "phase", "template"},
                            exclude_none=True,
                            exclude_unset=True,
                        ),
                        "name": well.name,
                    }
                )
        return operations_dict
