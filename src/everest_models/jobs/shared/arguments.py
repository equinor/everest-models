import argparse
import functools
from functools import partial
from pathlib import Path
from sys import stdout
from typing import Callable, Dict, Iterator, Optional, Tuple, Type, TypeVar, Union

from pydantic import BaseModel
from ruamel.yaml.comments import CommentedMap, CommentedSeq
from typing_extensions import TypeAlias

from everest_models.jobs.shared.models.base_config.base import ModelConfig
from everest_models.jobs.shared.models.base_config.introspective import is_related

from .io_utils import dump_yaml
from .models import Wells
from .validators import (
    is_writable_path,
    parse_file,
    valid_ecl_summary,
    valid_input_file,
)

T = TypeVar("T", bound=BaseModel)
Parser: TypeAlias = Union[argparse.ArgumentParser, argparse._ArgumentGroup]


class SchemaAction(argparse.Action):
    _models = {}

    @classmethod
    def register_models(cls, models: Dict[str, Type[T]]) -> None:
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

    def __call__(self, parser: argparse.ArgumentParser, *_):
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


class ArgumentDefaultsHelpFormatter(argparse.ArgumentDefaultsHelpFormatter):
    def _get_help_string(self, action):
        return (
            action.help
            if action.default is None or isinstance(action.default, bool)
            else super()._get_help_string(action)
        )


def add_input_argument(parser: Parser, *args, **kwargs) -> None:
    """Add input argument to parser.

    - Set type to 'valid_input_file' function caller
    - Set required to True

    Args:
        parser (argparse.ArgumentParser): Argument parser
    """
    parser.add_argument(
        "-i",
        "--input",
        *args,
        type=valid_input_file,
        required=True,
        **kwargs,
    )


def add_lint_argument(parser: Parser) -> None:
    """Add optional lint argument to parser.

    - Set action to 'store_true'

    Args:
        parser (argparse.ArgumentParser): Argument parser
    """
    parser.add_argument(
        "--lint",
        action="store_true",
        help="Lints all given input (file) arguments with no data transformation.",
    )


def add_file_schemas(parser: Parser) -> None:
    """Add optional schema argument to parser

    - Set action to 'SchemaAction'

    Args:
        parser (argparse.ArgumentParser): Argument parser
    """
    parser.add_argument(
        "--schema",
        nargs=0,
        action=SchemaAction,
        help="Output schema(s) for file parameter(s)",
    )


def add_summary_argument(parser: Parser, *, func: Optional[Callable] = None) -> None:
    """Add summary argument to parser.

    - Set type to 'func' or 'valid_ecl_summary' function caller
    - Set required to 'True'

    Args:
        parser (argparse.ArgumentParser): Argument parser
        func (Callable, optional): Function caller to use for type. Defaults to None.
    """
    parser.add_argument(
        "-s",
        "--summary",
        type=func or valid_ecl_summary,
        required=True,
        help="Eclipse summary file",
    )


def add_wells_input_argument(
    parser: Parser,
    *,
    required: bool = True,
    schema: Type[T] = Wells,
    **kwargs,
) -> None:
    """Add wells argument to parser

    - Set type to 'parse_file' function caller

    Args:
        parser (argparse.ArgumentParser): Argument parser
        required (bool, optional): Is this argument required?. Defaults to True.
        schema (models.BaseConfig, optional):
            Parser and validation schema to use. Defaults to models.WellListModel.
    """
    arg = ["-i", "--input"]
    parser.add_argument(
        *arg,
        type=partial(parse_file, schema=schema),
        required=required,
        **kwargs,
    )
    SchemaAction.register_models({"/".join(arg): schema})


def add_output_argument(parser: Parser, *, required: bool = True, **kwargs) -> None:
    """Add output argument to parser

    - Set type to 'is_writable_path' function caller

    Args:
        parser (argparse.ArgumentTypeError): Argument parser
        required (bool, optional): Is this argument required?. Defaults to True.
    """
    parser.add_argument(
        "-o",
        "--output",
        required=required,
        type=is_writable_path,
        **kwargs,
    )


def get_parser(**kwargs) -> Tuple[argparse.ArgumentParser, argparse._ArgumentGroup]:
    """Create a custom argument parser.

    - Add default argument values into help menu
    - Create a required named argument group

    Returns:
        Tuple[argparse.ArgumentParser, argparse._ArgumentGroup]:
            Custom argument parser and its required group
    """
    kwargs.setdefault("formatter_class", ArgumentDefaultsHelpFormatter)
    parser = argparse.ArgumentParser(**kwargs)
    return parser, parser.add_argument_group("required named arguments")


def bootstrap_parser(func):
    """Bootstrap argument parser

    - Add default argument values into help menu
    - Add lint argument to parser
    - Add schema argument to parser
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        parser = func(*args, **kwargs)
        add_lint_argument(parser)
        add_file_schemas(parser)
        return parser

    return wrapper
