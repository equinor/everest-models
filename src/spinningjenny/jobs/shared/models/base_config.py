import pathlib
import sys
import typing

import ruamel.yaml as yaml
from pydantic import BaseModel, Extra
from pydantic.fields import ModelField

from spinningjenny.jobs.shared.converters import path_to_str


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
    def _field_properties(
        cls, model: ModelField, field_property: typing.Dict[str, str]
    ):
        if field_property is None:
            field_property = cls._get_field_property(model.name)
        return {
            "required": model.required,
            "type": field_property["type"],
            **({"default": model.default} if model.default else {}),
            **({"format": format} if (format := field_property.get("format")) else {}),
        }

    @classmethod
    def _get_field_property(cls, name: str) -> typing.Optional[typing.Dict[str, str]]:
        return cls.schema()["properties"][name] if name != "__root__" else None

    @classmethod
    def _get_sub_schema(
        cls,
        field: str,
        field_property: typing.Dict[str, str],
        typ: typing.Union[type, BaseModel],
    ):
        sub_schema = (
            typ.help_schema()
            if issubclass(typ, BaseModel)
            else field_property["items"]["type"]
        )
        return (
            [sub_schema]
            if field == "__root__"
            or ((typ := field_property.get("type")) is not None and typ == "array")
            else sub_schema
        )

    @classmethod
    def _help_fields_schema(cls):
        for field, model in cls.__fields__.items():
            field_property = cls._get_field_property(model.name)
            yield field, cls._get_sub_schema(
                field, field_property, model.type_
            ) if model.is_complex() else cls._field_properties(model, field_property)

    @classmethod
    def help_schema(cls, argument_name: str = None) -> typing.Union[dict, list]:
        fields = dict(cls._help_fields_schema())
        if (root := fields.pop("__root__", None)) is not None:
            fields = root
        if argument_name is not None:
            fields = dict(argument=argument_name, fields=fields)
        return fields

    @classmethod
    def help_schema_yaml(cls, argument_name: str = None) -> None:
        yml = yaml.YAML(typ="safe", pure=True)
        yml.indent(mapping=3, sequence=2, offset=0)
        yml.dump(cls.help_schema(argument_name), sys.stdout)


class BaseFrozenConfig(BaseConfig):
    class Config:
        frozen = True
