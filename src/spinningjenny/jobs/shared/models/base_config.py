import inspect
import pathlib
import sys
import typing

from pydantic import BaseModel, Extra
from pydantic.fields import ModelField

from spinningjenny.jobs.shared import io_utils as io
from spinningjenny.jobs.shared.converters import path_to_str
from spinningjenny.jobs.shared.models.phase import BaseEnum


def _is_complex_field(value: typing.Any) -> bool:
    return inspect.isclass(value) and any(
        issubclass(value, klass) for klass in (BaseEnum, dict)
    )


class BaseConfig(BaseModel):
    """Mutable custom pydantic BaseModel configuration with schema specification renderer."""

    class Config:
        validate_assignment = True
        arbitrary_types_allowed = False
        underscore_attrs_are_private = True
        extra = Extra.forbid
        json_encoders = {pathlib.Path: path_to_str}

    def json_dump(self, output: pathlib.Path) -> None:
        """Write instance state to a JSON file.

        Args:
            output (pathlib.Path): file to write to
        """
        output.write_text(
            self.json(
                indent=2,
                separators=(",", ": "),
                exclude_none=True,
                exclude_unset=True,
                sort_keys=True,
            )
        )

    @classmethod
    def _field_properties(cls, model: ModelField) -> typing.Dict[str, typing.Any]:
        return {
            "required": model.required,
            **({"default": model.default} if model.default else {}),
            **{
                field: value
                for field, value in cls._get_field_property(model.name).items()
                if field in ("type", "oneOf", "format")
            },
        }

    @classmethod
    def _get_field_property(cls, name: str) -> typing.Optional[typing.Dict[str, str]]:
        schema = cls.schema()
        return (
            schema["properties"][name]
            if name != "__root__"
            else {"type": schema["type"]}
        )

    @classmethod
    def _unravel_nested(cls, typ):
        def builtin_types_to_string(builtin):
            if _is_complex_field(builtin):
                return builtin.value_type()
            return {int: "integer", str: "string"}.get(builtin) or builtin.__name__

        if inspect.isclass(typ) and issubclass(typ, BaseModel):
            return typ.help_schema()
        origin = typing.get_origin(typ)
        args = typing.get_args(typ)
        if origin is dict:
            key, value = args
            return {builtin_types_to_string(key): cls._unravel_nested(value)}
        if origin in (tuple, list):
            return [cls._unravel_nested(arg) for arg in args if arg is not Ellipsis]
        if origin is typing.Union:
            return {
                "one of": [
                    cls._unravel_nested(arg) for arg in args if arg is not Ellipsis
                ]
            }
        if origin is set:
            return [
                {"unique": True, "value": cls._unravel_nested(arg)}
                for arg in args
                if arg
            ]
        return builtin_types_to_string(typ)

    @classmethod
    def _help_fields_schema(cls):
        for field, model in cls.__fields__.items():
            value = (
                cls._unravel_nested(model.outer_type_)
                if model.is_complex()
                or _is_complex_field(model.outer_type_)
                or (
                    inspect.isclass(model.outer_type_)
                    and issubclass(model.outer_type_, BaseEnum)
                )
                or typing.get_origin(model.outer_type_) == typing.Union
                else cls._field_properties(model)
            )
            if typing.get_origin(model.outer_type_) == typing.Literal:
                literals = typing.get_args(model.outer_type_)
                if len(literals) == 1:
                    literals = literals[0]
                value["literal"] = literals
            yield field, value

    @classmethod
    def help_schema(cls, argument_name: str = None) -> typing.Union[dict, list]:
        """Generate a dictionary representation of the class specification schema.

        Args:
            argument_name (str, optional): Argument name that this schema belongs to. Defaults to None.

        Returns:
            typing.Union[dict, list]: Class specification schema
        """
        fields = dict(cls._help_fields_schema())
        if (root := fields.pop("__root__", None)) is not None:
            fields = root
        if argument_name is not None:
            fields = dict(arguments=argument_name, fields=fields)
        return fields

    @classmethod
    def help_schema_yaml(cls, argument_name: str = None) -> None:
        """Output class specification schema to standard out.

        Args:
            argument_name (str, optional): Argument name that this schema belongs to. Defaults to None.
        """
        io.dump_yaml(cls.help_schema(argument_name), sys.stdout, explicit=True)


class BaseFrozenConfig(BaseConfig):
    """Frozen custom pydantic BaseModel Configuration with schema specification renderer."""

    class Config:
        frozen = True


class DictRootMixin:
    """Dictionary mixin functions for pydantic models with dictionary __root__ fields"""

    def get(self, value, default=None):
        return self.__root__.get(value, default)

    def keys(self):
        return self.__root__.keys()

    def values(self):
        return self.__root__.values()

    def items(self):
        return self.__root__.items()

    def __iter__(self) -> typing.Iterator:
        return iter(self.__root__)

    def __getitem__(self, item):
        return self.__root__[item]

    def __len__(self) -> int:
        return len(self.__root__)
