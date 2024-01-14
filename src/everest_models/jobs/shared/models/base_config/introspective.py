from collections.abc import Collection, Mapping, Sequence
from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from inspect import isclass
from pathlib import Path
from typing import Any, Optional, Type, get_args, get_origin

from pydantic import BaseModel
from pydantic.fields import FieldInfo
from pydantic_core import PydanticUndefined
from ruamel.yaml.comments import CommentedMap, CommentedSeq

__all__ = ["builtin_datatypes", "build_yaml_structure"]


INLINE_REPLACE = "← REPLACE"


@dataclass
class CommentedObject:
    value: Any
    comment: Optional[str] = None
    inline_comment: Optional[str] = None


def _is_related(value: Any, typ: Type) -> bool:
    return (isclass(value) and issubclass(value, typ)) or isinstance(value, typ)


def builtin_datatypes(value: Any) -> str:
    if _is_related(value, bool):
        return "boolean"
    if _is_related(value, int):
        return "integer"
    if _is_related(value, float):
        return "number"
    if _is_related(value, str):
        return "string"
    if _is_related(value, BaseModel):
        return f"{value.__name__} map"
    if _is_related(value, Enum):
        try:
            value = value.value
        except AttributeError:
            value = next(iter(value)).value
        return builtin_datatypes(value)
    if origin := get_origin(value):
        string = (
            f"({items})"
            if ","
            in (
                items := ", ".join(
                    builtin_datatypes(arg)
                    for arg in get_args(value)
                    if arg is not Ellipsis
                )
            )
            else items
        )
        if _is_related(origin, Sequence):
            return f"a array of {string}"
        if _is_related(origin, Mapping):
            return f"a mapping of {string}"
        if _is_related(origin, Collection):
            return f"a collection of {string}"
    return value.__name__


def _example_types(value: Any) -> str:
    prefix = "Examples"
    if _is_related(value, int):
        return f"{prefix}: 1, 1.34E5, 1.34e5"
    if _is_related(value, float):
        return f"{prefix}: .1, 1. 1 1.0, 1.34E-5, 1.34e-5"
    if _is_related(value, str):
        return f"{prefix}: a string value"
    if _is_related(value, bool):
        return "Choices: true, false"
    if _is_related(value, Path):
        return f"{prefix}: /path/to/file.ext, /path/to/dirictory/"
    if _is_related(value, date) or _is_related(value, datetime):
        return f"{prefix}: 2024-01-31, 2024-01-31T11:06"
    if _is_related(value, Enum):
        return "Choices: " + ", ".join(str(entry.value) for entry in value)
    return ""


def _build_comment(info: FieldInfo) -> str:
    if info.default_factory:
        default = typ = info.default_factory()
    if info.default is PydanticUndefined or info.default is None:
        default = "null" if info.default is None else None
        typ = info.annotation
    else:
        default = typ = info.default

    default = default.value if _is_related(default, Enum) else default  # type: ignore
    typ = typ if typ is None else builtin_datatypes(typ)
    examples = (
        ("Examples: " + ", ".join(map(str, info.examples)))
        if info.examples
        else _example_types(info.annotation)
    )
    return "\n" + "\n".join(
        filter(
            lambda x: x,
            (  # type: ignore
                info.description,
                f"Datatype: {typ or '_'}",
                examples,
                f"Default: {default}" if default else default,
            ),
        )
    )


def build_yaml_structure(data: Any, level: int = 0):
    if isinstance(data, Mapping):
        result = CommentedMap()
        for key, value in data.items():
            if isinstance(value, CommentedObject):
                sub_result = build_yaml_structure(value.value, level + 1)
                if value.comment:
                    result.yaml_set_comment_before_after_key(
                        key, before=value.comment, indent=level * 2
                    )
                if value.inline_comment:
                    result.yaml_add_eol_comment(value.inline_comment, key=key)
                result[key] = sub_result
            else:
                result[key] = build_yaml_structure(value)
        return result
    elif isinstance(data, Sequence) and not isinstance(data, str):
        result = CommentedSeq()
        for item in data:
            if isinstance(item, CommentedObject):
                # Inline comments for list items are handled differently
                if item.inline_comment:
                    result.append(item.value)
                    result.yaml_add_eol_comment(item.inline_comment, len(result) - 1)
                else:
                    result.append(build_yaml_structure(item.value, level + 1))
            else:
                result.append(build_yaml_structure(item, level + 1))
        return result
    elif isinstance(data, CommentedObject):
        # For standalone CommentedObject not in a collection
        return build_yaml_structure(data.value, level)
    else:
        return "null" if data is None else data() if callable(data) else data


def _base_model_comment(arg: Any, comment: Optional[str]) -> CommentedObject:
    return CommentedObject(
        **(
            {"value": arg.introspective_data()}
            if _is_related(arg, BaseModel)  # TODO: ModelConfig
            else {"value": "...", "inline_comment": INLINE_REPLACE}
        ),
        comment=comment,
    )


def parse_field_info(info: FieldInfo) -> Any:
    comment = _build_comment(info)
    if origin := get_origin(info.annotation):
        if _is_related(origin, Sequence):
            return [
                _base_model_comment(arg, comment)
                for arg in get_args(info.annotation)
                if arg is not Ellipsis
            ]
        if _is_related(origin, Mapping):
            return {
                field: _base_model_comment(model, comment)
                for field, model in get_args(info.annotation)
                if model is not Ellipsis
            }
    if _is_related(info.annotation, BaseModel):  # TODO: ModelConfig
        return CommentedObject(info.annotation.introspective_data(), comment)  # type: ignore
    if info.default_factory is not None:
        return CommentedObject(info.default_factory, comment)
    if info.default is PydanticUndefined:
        return CommentedObject("...", comment, INLINE_REPLACE)
    return CommentedObject(
        info.default.value if isinstance(info.default, Enum) else info.default, comment
    )


def parse_annotation(annotation: Any) -> Any:
    if _is_related(annotation, BaseModel):
        return CommentedObject(annotation.introspective_data())

    origin = get_origin(annotation)
    args = get_args(annotation)

    if issubclass(origin, Mapping):
        key, value = args
        return {f"<{builtin_datatypes(key)}>": CommentedObject(parse_annotation(value))}
    if issubclass(origin, Sequence):
        return [
            CommentedObject(parse_annotation(arg))
            for arg in args
            if arg is not Ellipsis
        ]
    return CommentedObject("...", inline_comment=INLINE_REPLACE)
