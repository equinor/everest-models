from collections import defaultdict
from typing import Tuple

from pydantic import ConfigDict, Field, FilePath, PlainSerializer
from typing_extensions import Annotated

from everest_models.jobs.shared.converters import path_to_str
from everest_models.jobs.shared.models import (
    OPERATIONS_FIELD_ATTRIBUTE,
    Operation,
    Well,
)
from everest_models.jobs.shared.models import (
    Wells as _Wells,
)


class _Operation(Operation):
    model_config = ConfigDict(title="Operation")

    template: Annotated[
        FilePath,
        PlainSerializer(path_to_str, when_used="unless-none"),
        Field(description="file path to jinja template"),
    ]


class _Well(Well):
    model_config = ConfigDict(title="Well")

    operations: Annotated[  # type: ignore
        Tuple[_Operation, ...],
        Field(**OPERATIONS_FIELD_ATTRIBUTE),
    ]


class Wells(_Wells):
    root: Tuple[_Well, ...]  # type: ignore

    def dated_operations(self):
        operations_dict = defaultdict(list)
        for well in self:
            for operation in well.operations:
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
