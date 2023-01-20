import argparse
from functools import partial
from typing import Callable, Dict, Tuple

from spinningjenny.jobs.shared import models
from spinningjenny.jobs.shared.validators import (
    is_writable_path,
    parse_file,
    valid_ecl_summary,
    valid_input_file,
)


class SchemaAction(argparse.Action):
    _models = {}

    @classmethod
    def register_single_model(cls, argument: str, model: models.BaseConfig):
        cls._models.update({argument: model})

    @classmethod
    def register_models(cls, items: Dict[str, models.BaseConfig]):
        cls._models.update(items)

    def __call__(self, parser, namespace, values, option_string):
        for argument, model in self._models.items():
            model.help_schema_yaml(argument)
        parser.exit()


class ArgumentDefaultsHelpFormatter(argparse.ArgumentDefaultsHelpFormatter):
    def _get_help_string(self, action):
        return (
            action.help
            if action.default is None or isinstance(action.default, bool)
            else super()._get_help_string(action)
        )


def add_input_argument(parser: argparse.ArgumentParser, *args, **kwargs):
    parser.add_argument(
        "-i",
        "--input",
        type=valid_input_file,
        required=True,
        *args,
        **kwargs,
    )


def add_lint_argument(parser: argparse.ArgumentParser):
    parser.add_argument(
        "--lint",
        action="store_true",
        help="Lints all given input (file) arguments with no data transformation.",
    )


def add_file_schemas(parser: argparse.ArgumentParser):
    parser.add_argument(
        "--schemas",
        nargs=0,
        action=SchemaAction,
        help="Output all file schemas that are taken as input parameters.",
    )


def add_summary_argument(parser: argparse.ArgumentParser, *, func: Callable = None):
    parser.add_argument(
        "-s",
        "--summary",
        type=func or valid_ecl_summary,
        required=True,
        help="Ecl summary file",
    )


def add_wells_input_argument(
    parser: argparse.ArgumentParser,
    *,
    required: bool = True,
    schema: models.BaseConfig = models.WellListModel,
    **kwargs,
):
    arg = ["-i", "--input"]
    parser.add_argument(
        *arg,
        type=partial(parse_file, schema=schema),
        required=required,
        **kwargs,
    )
    SchemaAction.register_single_model("/".join(arg), models.WellListModel)


def add_output_argument(
    parser: argparse.ArgumentTypeError, *, required: bool = True, **kwargs
):
    parser.add_argument(
        "-o",
        "--output",
        required=required,
        type=is_writable_path,
        **kwargs,
    )


def get_parser(**kwargs) -> Tuple[argparse.ArgumentParser, argparse._ArgumentGroup]:
    kwargs.setdefault("formatter_class", ArgumentDefaultsHelpFormatter)
    parser = argparse.ArgumentParser(**kwargs)
    return parser, parser.add_argument_group("required named arguments")


def bootstrap_parser(
    **kwargs,
) -> Tuple[argparse.ArgumentParser, argparse._ArgumentGroup]:
    parser, required_group = get_parser(**kwargs)
    add_lint_argument(parser)
    add_file_schemas(parser)
    return parser, required_group
