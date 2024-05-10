import pathlib
from inspect import isclass
from typing import Any, Type


def is_related(value: Any, typ: Type) -> bool:
    return issubclass(value, typ) if isclass(value) else isinstance(value, typ)


def rescale_value(value, lower, upper, new_lower, new_upper):
    """Rescale a value with bounds [lower, upper] to the range [new_lower, new_upper]"""
    return (value - lower) * (new_upper - new_lower) / (upper - lower) + new_lower


def path_to_str(path: pathlib.Path):
    return f"{'' if path.is_absolute() else './'}{path}"
