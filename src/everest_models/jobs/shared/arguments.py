import argparse
import functools
from functools import partial
from typing import Callable, Optional, Tuple, Type, TypeVar, Union

from pydantic import BaseModel
from typing_extensions import TypeAlias

from .models import Wells
from .parsers import SchemaAction
from .validators import (
    is_writable_path,
    parse_file,
    valid_ecl_summary,
    valid_input_file,
)

T = TypeVar("T", bound=BaseModel)
Parser: TypeAlias = Union[argparse.ArgumentParser, argparse._ArgumentGroup]


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
    skip_type = kwargs.pop("skip_type") if "skip_type" in kwargs else False
    parser.add_argument(
        "-i",
        "--input",
        *args,
        type=valid_input_file if not skip_type else str,
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
        help=(
            "Optional argument to activate verification of validity of all "
            "given input (file) arguments without actually executing the "
            "forward model (i.e., no data transformation, no output calculation)."
        ),
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
        help=(
            "Optional argument to generate schemas of the configuration "
            "file with its expected structure to facilitate its setting up by the user. "
        ),
    )


def add_summary_argument(
    parser: Parser, *, func: Optional[Callable] = None, **kwargs
) -> None:
    """Add summary argument to parser.

    - Set type to 'func' or 'valid_ecl_summary' function caller
    - Set required to 'True'

    Args:
        parser (argparse.ArgumentParser): Argument parser
        func (Callable, optional): Function caller to use for type. Defaults to None.
    """
    skip_type = kwargs.pop("skip_type") if "skip_type" in kwargs else False
    parser.add_argument(
        "-s",
        "--summary",
        type=func or valid_ecl_summary if not skip_type else str,
        required=True,
        help="Eclipse summary file",
    )


def add_wells_input_argument(
    parser: Parser,
    *,
    required: bool = True,
    schema: Type[T] = Wells,
    arg: Tuple[str, str] = ("-i", "--input"),
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
    skip_type = kwargs.pop("skip_type") if "skip_type" in kwargs else False
    parser.add_argument(
        *arg,
        type=partial(parse_file, schema=schema) if not skip_type else str,
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
    skip_type = kwargs.pop("skip_type") if "skip_type" in kwargs else False
    parser.add_argument(
        "-o",
        "--output",
        required=required,
        type=is_writable_path if not skip_type else str,
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
