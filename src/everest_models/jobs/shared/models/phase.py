from enum import Enum


class PhaseEnum(Enum):
    WATER = "WATER"
    GAS = "GAS"
    OIL = "OIL"

    @classmethod
    def _missing_(cls, value):
        for member in cls:
            if isinstance(value, str) and member.value == value.upper():
                return member
