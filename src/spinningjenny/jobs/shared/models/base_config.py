import inspect
import pathlib
import sys
import typing

import ruamel.yaml as yaml
from pydantic import BaseModel, Extra
from pydantic.fields import ModelField

from spinningjenny.jobs.shared.converters import path_to_str
from spinningjenny.jobs.shared.models.phase import BaseEnum


class BaseConfig(BaseModel):
    class Config:
        validate_assignment = True
        arbitrary_types_allowed = False
        extra = Extra.forbid
        json_encoders = {
            pathlib.Path: path_to_str,
        }

    def json_dump(self, output: pathlib.Path) -> None:
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
    def _field_properties(cls, model: ModelField):
        field_property = cls._get_field_property(model.name)
        return {
            "required": model.required,
            "type": field_property["type"],
            **({"default": model.default} if model.default else {}),
            **({"format": format} if (format := field_property.get("format")) else {}),
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
            if inspect.isclass(builtin) and issubclass(builtin, BaseEnum):
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
        return builtin_types_to_string(typ)

    @classmethod
    def _help_fields_schema(cls):
        for field, model in cls.__fields__.items():
            value = (
                cls._unravel_nested(model.outer_type_)
                if model.is_complex()
                or (
                    inspect.isclass(model.outer_type_)
                    and issubclass(model.outer_type_, BaseEnum)
                )
                else cls._field_properties(model)
            )
            yield field, value

    @classmethod
    def help_schema(cls, argument_name: str = None) -> typing.Union[dict, list]:
        fields = dict(cls._help_fields_schema())
        if (root := fields.pop("__root__", None)) is not None:
            fields = root
        if argument_name is not None:
            fields = dict(arguments=argument_name, fields=fields)
        return fields

    @classmethod
    def help_schema_yaml(cls, argument_name: str = None) -> None:
        yml = yaml.YAML(typ="safe", pure=True)
        yml.explicit_start = True
        yml.indent(mapping=3, sequence=2, offset=0)
        yml.explicit_end = True
        yml.dump(cls.help_schema(argument_name), sys.stdout)


class BaseFrozenConfig(BaseConfig):
    class Config:
        frozen = True


class DictRootMixin:
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
