from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from pathlib import Path
from typing import Any, Literal, Optional, Union, get_args, get_origin

from pydantic import BaseModel
from pydantic.fields import FieldInfo
from pydantic_core import PydanticUndefined
from ruamel.yaml.comments import CommentedMap, CommentedSeq

from everest_models.jobs.shared import is_related

__all__ = ["builtin_datatypes", "build_yaml_structure"]


INLINE_REPLACE = "← REPLACE"


@dataclass
class CommentedObject:
    value: Any
    comment: Optional[str] = None
    inline_comment: Optional[str] = None


def builtin_datatypes(value: Any) -> str:
    if value is None or value is type(None):
        return ""
    if is_related(value, bool):
        return "boolean"
    if is_related(value, int):
        return "integer"
    if is_related(value, float):
        return "number"
    if is_related(value, str):
        return "string"
    if is_related(value, BaseModel):
        return f"{value.__name__.lstrip('_')} map"
    if is_related(value, Enum):
        try:
            value = value.value
        except AttributeError:
            value = next(iter(value)).value
        return builtin_datatypes(value)
    # check for nametuples
    if is_related(value, Sequence) and hasattr(value, "_field_types"):
        return str([builtin_datatypes(type_) for type_ in value._field_types.values()])
    if origin := get_origin(value):
        if origin is Literal:
            return ", ".join(item for item in get_args(value))
        string = ", ".join(
            builtin_datatypes(arg) for arg in get_args(value) if arg is not Ellipsis
        )
        if origin is Union:
            return string.rstrip(", ").replace(",", " or")
        if is_related(origin, set):
            return f"unique values [{string}]"
        if is_related(origin, Sequence):
            return f"[{string}]"
        if is_related(origin, Mapping):
            return "{" + string.replace(",", ":") + "}"
        return string
    return value.__name__


def _example_types(value: Any) -> str:
    prefix = "Examples"
    if is_related(value, bool):
        return "Choices: true, false"
    if is_related(value, int):
        return f"{prefix}: 1, 1.34E5, 1.34e5"
    if is_related(value, float):
        return f"{prefix}: .1, 1., 1, 1.0, 1.34E-5, 1.34e-5"
    if is_related(value, str):
        return f"{prefix}: a string value"
    if is_related(value, Path):
        return f"{prefix}: /path/to/file.ext, /path/to/dirictory/"
    if is_related(value, date) or is_related(value, datetime):
        return f"{prefix}: 2024-01-31, 2024-01-31T11:06"
    if is_related(value, Enum):
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

    default = default.value if is_related(default, Enum) else default  # type: ignore
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
                f"Required: {info.is_required()}",
                default if default is None else f"Default: {default}",
            ),
        )
    )


def build_yaml_structure(data: Any, level: int = 0):
    """
    This function recursively builds a commented YAML structure from CommentedObjects.

    It handles different types of containers, mappings, sequences, and CommentedObjects.
    recursively break containers down to the essientials and and insert into yaml
    container structure.
    For mappings, it creates a CommentedMap. If a value is a CommentedObject,
    For sequences, it creates a CommentedSeq. If an item is a CommentedObject,
    For standalone CommentedObject, extract elements (comments and value) from object
    If the data is callable (default_factory), envoke it

    Note: CommentedObject classes for handling comments in the YAML structure.

    Parameters:
    data (Any): Nested container of CommentedObjects.
    level (int): The current level of nesting in the YAML structure. Default is 0.

    Returns:
    Union[CommentedMap, CommentedSeq, Any]: The built YAML structure.

    Raises:
    None
    """

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
                result[key] = build_yaml_structure(value, level + 1)
        return result
    if isinstance(data, Sequence) and not isinstance(data, str):
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
    if isinstance(data, CommentedObject):
        # For standalone CommentedObject not in a collection
        return build_yaml_structure(data.value, level)
    return data() if callable(data) else data


def parse_annotation(annotation: Any, minimal: bool, no_comment: bool) -> Any:
    if is_related(annotation, BaseModel):
        return annotation.introspective_data(minimal, no_comment)

    origin = get_origin(annotation)
    args = get_args(annotation)

    if is_related(origin, Mapping):
        key, value = args
        return {
            f"<{builtin_datatypes(key)}>": parse_annotation(value, minimal, no_comment)
        }
    if is_related(origin, Sequence):
        return [
            parse_annotation(arg, minimal, no_comment)
            for arg in args
            if arg is not Ellipsis
        ]
    return "..."


def _parse_field_info(info: FieldInfo, minimal: bool, no_comment: bool) -> Any:
    if get_origin(info.annotation) or is_related(info.annotation, BaseModel):
        return parse_annotation(info.annotation, minimal, no_comment)
    if info.default_factory is not None:
        return info.default_factory
    if info.default is PydanticUndefined:
        return "..."
    return info.default.value if isinstance(info.default, Enum) else info.default


def parse_field_info(info: FieldInfo, minimal: bool, no_comment: bool) -> Any:
    """
    Parses the field information based on the provided parameters.

    Args:
    info (FieldInfo): The field information to be parsed.

    minimal (bool): A flag indicating only parse required values,
    used for nested recursion calls back to `introspective_data` method
    True: only required fields are parsed
    False: all fields are parsed

    no_comment (bool): A flag indicating whether comments should be included,
    False: will build comment string from parsed info data
    and package the comment together with defualt value into a CommentedObject
    True: only default value is extracted

    Returns:
    Any: default value if requested with comments.

    Raises:
    None
    """
    value = _parse_field_info(info, minimal, no_comment)
    if no_comment:
        return value
    return CommentedObject(
        value,
        _build_comment(info),
        INLINE_REPLACE if is_related(value, str) and value == "..." else None,
    )
