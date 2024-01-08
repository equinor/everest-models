import inspect
import pathlib
import sys
import typing

from pydantic import BaseModel, ConfigDict
from pydantic.fields import FieldInfo

from everest_models.jobs.shared import io_utils as io
from everest_models.jobs.shared.converters import path_to_str
from everest_models.jobs.shared.models.phase import BaseEnum


def _is_complex_field(value: typing.Any) -> bool:
    return inspect.isclass(value) and any(
        issubclass(value, klass) for klass in (BaseEnum, dict, tuple, list, set)
    )


class BaseConfig(BaseModel):
    """Mutable custom pydantic BaseModel configuration with schema specification renderer."""

    # Check https://docs.pydantic.dev/dev-v2/migration/#changes-to-config for more information.
    model_config = ConfigDict(
        validate_assignment=True,
        arbitrary_types_allowed=False,
        json_encoders={pathlib.Path: path_to_str},
    )

    def json_dump(self, output: pathlib.Path) -> None:
        """Write instance state to a JSON file.

        Args:
            output (pathlib.Path): file to write to
        """
        output.write_text(
            self.model_dump_json(
                indent=2,
                exclude_none=True,
                exclude_unset=True,
            )
        )

    @classmethod
    def _field_properties(cls, field, info: FieldInfo) -> typing.Dict[str, typing.Any]:
        return {
            "required": info.is_required(),
            **({"default": info.default} if info.default else {}),
            **{
                field: value
                for field, value in cls._get_field_property(field).items()
                if field in ("type", "oneOf", "format")
            },
        }

    @classmethod
    def _get_field_property(cls, name: str) -> typing.Optional[typing.Dict[str, str]]:
        schema = cls.model_json_schema()
        return (
            schema["properties"][name] if name != "root" else {"type": schema["type"]}
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
        if origin is set:
            return [
                {"unique": True, "value": cls._unravel_nested(arg)}
                for arg in args
                if arg
            ]
        if len(args) == 2 and args[1] is type(None):
            return {"format": cls._unravel_nested(args[0]), "required": False}
        if origin is typing.Union:
            return {
                "one of": [
                    cls._unravel_nested(arg) for arg in args if arg is not Ellipsis
                ]
            }

        return builtin_types_to_string(typ)

    @classmethod
    def _help_fields_schema(cls):
        for field, info in cls.model_fields.items():
            value = (
                cls._unravel_nested(info.annotation)
                if _is_complex_field(typing.get_origin(info.annotation))
                or (
                    inspect.isclass(info.annotation)
                    and issubclass(info.annotation, BaseEnum)
                )
                or typing.get_origin(info.annotation) == typing.Union
                or inspect.isclass(info.annotation)
                and issubclass(info.annotation, BaseModel)
                else cls._field_properties(field, info)
            )
            if typing.get_origin(info.annotation) == typing.Literal:
                literals = typing.get_args(info.annotation)
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
        if (root := fields.pop("root", None)) is not None:
            fields = root
        if argument_name is not None:
            fields = {"arguments": argument_name, "fields": fields}
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

    model_config = ConfigDict(frozen=True)


class DictRootMixin:
    """Dictionary mixin functions for pydantic models with dictionary __root__ fields"""

    def get(self, value, default=None):
        return self.root.get(value, default)

    def keys(self):
        return self.root.keys()

    def values(self):
        return self.root.values()

    def items(self):
        return self.root.items()

    def __iter__(self) -> typing.Iterator:
        return iter(self.root)

    def __getitem__(self, item):
        return self.root[item]

    def __len__(self) -> int:
        return len(self.root)
