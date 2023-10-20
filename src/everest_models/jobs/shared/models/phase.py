import abc
import enum
from typing import Any, Dict


class _ABCEnumMeta(enum.EnumMeta, abc.ABCMeta):
    pass


class BaseEnum(enum.Enum, metaclass=_ABCEnumMeta):
    @abc.abstractclassmethod
    def value_type(cls) -> str:
        pass


class PhaseEnum(BaseEnum):
    WATER = "WATER"
    GAS = "GAS"
    OIL = "OIL"

    @classmethod
    def value_type(cls) -> Dict[str, Any]:
        return {"type": "string", "choices": [item.value for item in cls]}

    @classmethod
    def _missing_(cls, value):
        for member in cls:
            if member.value == value.upper():
                return member
