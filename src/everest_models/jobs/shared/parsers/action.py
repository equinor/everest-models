from argparse import Action, ArgumentParser
from pathlib import Path
from sys import stdout
from typing import (
    Dict,
    Iterator,
    Tuple,
    Type,
    Union,
)

from ruamel.yaml.comments import CommentedMap, CommentedSeq

from .. import is_related
from ..io_utils import dump_yaml
from ..models import Model, ModelConfig, Wells


class SchemaAction(Action):
    _models = {}

    @classmethod
    def register_models(cls, models: Dict[str, Type[Model]]) -> None:
        cls._models.update(models)

    @staticmethod
    def _model_specsifactions(
        argument: str, model: ModelConfig
    ) -> Union[CommentedSeq, CommentedMap]:
        data = model.commented_map()
        data.yaml_set_start_comment(
            f"{argument} specification:\n'...' are REQUIRED fields that needs replacing\n\n"
        )
        return data

    def _specification_iterator(
        self,
    ) -> Iterator[Tuple[str, ModelConfig, Union[CommentedSeq, CommentedMap]]]:
        return (
            (
                argument.split("/")[-1].lstrip("-"),
                model,
                self._model_specsifactions(argument, model),
            )
            for argument, model in self._models.items()
        )

    def __call__(self, parser: ArgumentParser, *_):
        for argument, model, data in self._specification_iterator():
            if self.dest in ("show", "schema"):
                print("\n\n")
                if is_related(model, Wells):
                    print(f"{argument} is Everest generated wells JSON file")
                    continue
                dump_yaml(data, stdout, explicit=True, default_flow_style=False)
            if self.dest == "init":
                if is_related(model, Wells):
                    continue
                path = Path(
                    f"{'_'.join(parser.prog.split()[:-1]).lower()}_{argument}.yml"
                )
                with path.open(mode="w") as fd:
                    dump_yaml(data, fd, default_flow_style=False)
                print(f"file `{path.resolve()}` created")

        parser.exit()
