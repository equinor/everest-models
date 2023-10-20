from typing import Dict, Iterator, Tuple

from pydantic import root_validator, validator

from everest_models.jobs.shared.models import BaseFrozenConfig, DictRootMixin, PhaseEnum


class Phase(BaseFrozenConfig):
    options: Tuple[PhaseEnum, ...] = None
    value: PhaseEnum = None

    @validator("options")
    def is_not_empty(cls, options):
        assert options is None or options, "Empty 'options' list"
        return options

    @root_validator
    def is_correct_phase_field(cls, values):
        assert (values.get("options") is None) ^ (
            values.get("value") is None
        ), "'options' key cannot be used in conjunction with 'value' key."
        return values

    def _optimum_index(self, optimizer_value: float, *, thresholds: Iterator) -> int:
        for index, threshold in enumerate(thresholds):
            if optimizer_value <= threshold:
                return index

    def optimum_value(self, optimizer_value: float) -> str:
        if optimizer_value is None:
            return self.value if self.value is None else self.value.value

        options_size = len(self.options)
        return self.options[
            self._optimum_index(
                optimizer_value,
                thresholds=(float(x + 1) / options_size for x in range(options_size)),
            )
        ].value


class Tolerance(BaseFrozenConfig):
    min: float = None
    max: float = None
    value: float = None

    @root_validator
    def is_correct_tolerance_field(cls, values):
        value_keys = {
            key for key, _ in filter(lambda x: x[1] is not None, values.items())
        }
        has_min = "min" in value_keys
        has_max = "max" in value_keys

        errors = []
        if "value" in value_keys and (has_min or has_max):
            errors.append("Either ['max', 'min'] PAIR or 'value' key, but not both.")
        if has_min ^ has_max:
            errors.append("'max' and 'min' must be in a pair")
        if (has_min and has_max) and values["max"] <= values["min"]:
            errors.append("'max' cannot be less or equal to 'min' value.")
        assert not errors, "\n".join(errors)

        return values

    def optimum_value(self, optimizer_value: float) -> float:
        """Min/max scaling of input (optimizer) value"""
        return (
            self.value
            if optimizer_value is None
            else optimizer_value * (self.max - self.min) + self.min
        )


class Constraints(BaseFrozenConfig):
    phase: Phase
    rate: Tolerance
    duration: Tolerance


class WellConstraintConfig(BaseFrozenConfig, DictRootMixin):
    """An 'immutable' well constraint configuration schema.

    The schema is a container for a two layers deep dictionary.
    First layer key is a string that represents the well name.
    Second layer key is an integer that represent the Configuration index
    """

    __root__: Dict[str, Dict[int, Constraints]]
