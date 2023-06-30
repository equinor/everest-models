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


def add_input_argument(parser: argparse.ArgumentParser, *args, **kwargs) -> None:
    """Add input argument to parser.

    - Set type to 'valid_input_file' function caller
    - Set required to True

    Args:
        parser (argparse.ArgumentParser): Argument parser
    """
    parser.add_argument(
        "-i",
        "--input",
        type=valid_input_file,
        required=True,
        *args,
        **kwargs,
    )


def add_lint_argument(parser: argparse.ArgumentParser) -> None:
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


def add_file_schemas(parser: argparse.ArgumentParser) -> None:
    """Add optional schema argument to parser

    - Set action to 'SchemaAction'

    Args:
        parser (argparse.ArgumentParser): Argument parser
    """
    parser.add_argument(
        "--schemas",
        nargs=0,
        action=SchemaAction,
        help="Output all file schemas that are taken as input parameters.",
    )


def add_summary_argument(
    parser: argparse.ArgumentParser, *, func: Callable = None
) -> None:
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
        help="Ecl summary file",
    )


def add_wells_input_argument(
    parser: argparse.ArgumentParser,
    *,
    required: bool = True,
    schema: models.BaseConfig = models.WellConfig,
    **kwargs,
) -> None:
    """Add wells argument to parser

    - Set type to 'parse_file' function caller

    Args:
        parser (argparse.ArgumentParser): Argument parser
        required (bool, optional): Is this argument required?. Defaults to True.
        schema (models.BaseConfig, optional): Parser and validation schema to use. Defaults to models.WellListModel.
    """
    arg = ["-i", "--input"]
    parser.add_argument(
        *arg,
        type=partial(parse_file, schema=schema),
        required=required,
        **kwargs,
    )
    SchemaAction.register_single_model("/".join(arg), models.WellConfig)


def add_output_argument(
    parser: argparse.ArgumentTypeError, *, required: bool = True, **kwargs
) -> None:
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
        Tuple[argparse.ArgumentParser, argparse._ArgumentGroup]: Custom argument parser and its required group
    """
    kwargs.setdefault("formatter_class", ArgumentDefaultsHelpFormatter)
    parser = argparse.ArgumentParser(**kwargs)
    return parser, parser.add_argument_group("required named arguments")


def bootstrap_parser(
    **kwargs,
) -> Tuple[argparse.ArgumentParser, argparse._ArgumentGroup]:
    """Bootstrap custom argument parser


    - Add default argument values into help menu
    - Add lint argument to parser
    - Add schema argument to parser
    - Create a required named argument group

    Returns:
        Tuple[argparse.ArgumentParser, argparse._ArgumentGroup]: Custom argument parser and its required group
    """
    parser, required_group = get_parser(**kwargs)
    add_lint_argument(parser)
    add_file_schemas(parser)
    return parser, required_group
