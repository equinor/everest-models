from inspect import isclass
from pathlib import Path
from typing import Any


def is_related(value: Any, typ: type) -> bool:
    return issubclass(value, typ) if isclass(value) else isinstance(value, typ)


def path_to_str(path: Path):
    return f"{'' if path.is_absolute() else './'}{path}"
