from argparse import Action, ArgumentParser, Namespace
from datetime import datetime
from pathlib import Path
from sys import stdout
from typing import (
    Any,
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


def _get_filepath(base_name: str, no_overwrite: bool, minimal: bool) -> Path:
    base_name = f"{'minimal_'if minimal else ''}{base_name}"
    return (
        config.with_name(f"{base_name}_{datetime.now().strftime('%Y-%m-%dT%H%M')}.yml")
        if (config := (Path.cwd() / base_name).with_suffix(".yml")).exists()
        and no_overwrite
        else config
    )


def _model_specsifactions(
    argument: str, model: ModelConfig, minimal: bool, no_comment: bool
) -> Union[Dict[str, Any], CommentedSeq, CommentedMap]:
    if no_comment:
        return model.introspective_data(minimal, no_comment)

    data = model.commented_map(minimal)
    data.yaml_set_start_comment(
        f"{argument} specification:\n'...' are REQUIRED fields that needs replacing\n\n"
    )
    return data


class SchemaAction(Action):
    _models = {}

    @classmethod
    def register_models(cls, models: Dict[str, Type[Model]]) -> None:
        cls._models.update(models)

    def _specification_iterator(
        self, minimal: bool, no_comment: bool
    ) -> Iterator[Tuple[str, ModelConfig, Union[CommentedSeq, CommentedMap]]]:
        return (
            (
                argument.split("/")[-1].lstrip("-"),
                model,
                _model_specsifactions(argument, model, minimal, no_comment),
            )
            for argument, model in self._models.items()
        )

    def __call__(self, parser: ArgumentParser, options: Namespace, *_):
        for argument, model, data in self._specification_iterator(
            # getattr is use to keep backward compatibility
            getattr(options, "minimal", False),
            getattr(options, "no_comment", False),
        ):
            if self.dest == "schema" or options.show:
                print("\n\n")
                if not is_related(model, Wells):
                    dump_yaml(data, stdout, explicit=True, default_flow_style=False)
            elif options.init:
                if is_related(model, Wells):
                    continue
                path = _get_filepath(
                    "_".join(parser.prog.split()[:-1]).lower() + f"_{argument}",
                    options.no_overwrite,
                    options.minimal,
                )
                with path.open(mode="w") as fd:
                    dump_yaml(data, fd, default_flow_style=False)
                print(f"file `{path.resolve()}` created")

        parser.exit()
