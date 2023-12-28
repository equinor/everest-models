from typing import List, Sequence, Tuple

from pydantic import Field, FilePath, computed_field
from typing_extensions import Annotated

from everest_models.jobs.shared.models import Operation as _Operation
from everest_models.jobs.shared.models import Well as _Well
from everest_models.jobs.shared.models import Wells as _Wells


class Operation(_Operation):
    template: Annotated[
        FilePath,
        Field(default=None, description="File path to jinja template"),
    ]


class Well(_Well):
    operations: Annotated[
        List[Operation],
        Field(default_factory=list, description="Sequence of operations", alias="ops"),
    ]

    # TODO: create an pydantic issue
    # NOTE: this is a pydantic workaround
    # not sure if its a issue or feature
    # but model_dump_json with both exclude_unset and by_alias set to true
    # will omit operations since its not the alias and the alias is unset
    @computed_field
    def ops(self) -> Sequence[Operation]:
        return self.operations


class Wells(_Wells):
    root: Tuple[Well, ...]
