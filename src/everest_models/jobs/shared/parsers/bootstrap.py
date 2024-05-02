import re
from argparse import (
    ArgumentDefaultsHelpFormatter,
    ArgumentParser,
    _ArgumentGroup,
    _SubParsersAction,
)
from datetime import date, timedelta
from functools import wraps
from typing import Callable, Dict, Optional, Protocol, Type, Union

from typing_extensions import TypeAlias

from ..models import Model
from .action import SchemaAction

Parser: TypeAlias = Union[ArgumentParser, _ArgumentGroup]


class CustomFormatter(ArgumentDefaultsHelpFormatter):
    def _get_help_string(self, action):
        return (
            action.help
            if action.default is None or isinstance(action.default, bool)
            else super()._get_help_string(action)
        )

    def _format_action(self, action):
        parts = super(CustomFormatter, self)._format_action(action)
        if isinstance(action, _SubParsersAction):
            return re.sub(r"^\s+{.*}\n", "", parts) or parts
        return parts


class ParserBuilder(Protocol):
    def __call__(
        self, parser: Parser, legacy: bool = False, lint: bool = False
    ) -> None:
        ...


def build_schema_sub_parser(schema: ArgumentParser) -> None:
    schema.add_argument(
        "--show",
        nargs=0,
        action=SchemaAction,
        help="write all user defined input file schematics to stdout",
    )
    schema.add_argument(
        "--init",
        nargs=0,
        action=SchemaAction,
        help="Initialize all needed configuration files",
    )


def bootstrap_parser(
    schemas: Optional[Dict[str, Type[Model]]] = None,
    deprication: Optional[date] = None,
    **argument_parser_params,
) -> Callable[
    [ParserBuilder],
    Callable[[], ArgumentParser],
]:
    """
    Decorator function for creating an command line argument parser

    NOTE: By giving a deprication date, you admit that the decorated function
    is either a legacy function or a derivitive of one.
    deprication date should be the day that the commit would be expected on komodo release

    Args:
        schemas (Optional[Dict[str, Type[ModelConfig]]]): input file schematics to be register
        for the `schema` sub parser actions
        deprication (Optional[date]): Date of feature deprication.
        This will put feature removal a year from given date
        **argument_parser_params: ArgumentParser keyword arguments.

    Returns:
        Callable[[ParserBuilder], Callable[[], ArgumentParser]]

    The decorator expects a callable that sets the arguments for `run` and `lint` sub parser action.

    Example usage:
    ```python
    @bootstrap_parser(
        schemas={"schema": MySchema},
        prog="My Program",
        description="does something",
    )
    def build_argument_parser(
        parser: ArgumentParser,
        legacy: bool = False,
        lint: bool = False,
    )-> None:
        # Add positional and optional arguments to the parser
        if legacy:
            # arguments that differ based on legacy
        if not lint:
            # Arguments to skip for linting

    parser = build_argument_parser()
    ```
    """

    def decorator(func: ParserBuilder) -> Callable[[], ArgumentParser]:
        if schemas:
            SchemaAction.register_models(schemas)

        @wraps(func)
        def wrapper() -> ArgumentParser:
            argument_parser_params.setdefault("formatter_class", CustomFormatter)
            main = ArgumentParser(**argument_parser_params)
            if deprication:
                func(
                    main.add_argument_group(
                        "legacy forward model usage",
                        description=(
                            f"This flat structure flat is depricated since {deprication}, "
                            f"and will be removed in the future {deprication + timedelta(weeks=52)} "
                            "for the command structure"
                        ),
                    ),
                    legacy=True,
                )
            sub_parser = main.add_subparsers(
                dest="command",
                title="Commands",
            )
            build_schema_sub_parser(
                sub_parser.add_parser(
                    "schema", help="Schematic description of input data files"
                )
            )
            func(sub_parser.add_parser("run", help="Forward model execution"))
            func(sub_parser.add_parser("lint", help="Static files analysis"), lint=True)
            return main

        return wrapper

    return decorator
