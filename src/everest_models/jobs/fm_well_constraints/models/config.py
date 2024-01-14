from typing import Dict, Iterator, Optional, Tuple, overload

from pydantic import Field, field_validator, model_validator
from typing_extensions import Annotated

from everest_models.jobs.shared.models import ModelConfig, PhaseEnum, RootModelConfig


class Phase(ModelConfig):
    options: Annotated[Tuple[PhaseEnum, ...], Field(default=None, description="")]
    value: Annotated[PhaseEnum, Field(default=None, description="")]

    @field_validator("options")
    @classmethod
    def is_not_empty(cls, options):
        assert options is None or options, "Empty 'options' list"
        return options

    @model_validator(mode="before")
    @classmethod
    def is_correct_phase_field(cls, values):
        assert (values.get("options") is None or values.get("options") == []) ^ (
            values.get("value") is None
        ), "'options' key cannot be used in conjunction with 'value' key."
        return values

    def _optimum_index(self, optimizer_value: float, *, thresholds: Iterator) -> int:
        return next(
            index
            for index, threshold in enumerate(thresholds)
            if optimizer_value <= threshold
        )

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


class Tolerance(ModelConfig):
    min: Annotated[float, Field(default=None, description="")]
    max: Annotated[float, Field(default=None, description="")]
    value: Annotated[float, Field(default=None, description="")]

    @model_validator(mode="before")
    @classmethod
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

    def optimum_value(self, optimizer_value: Optional[float]) -> float:
        """Min/max scaling of input (optimizer) value"""
        return (
            self.value
            if optimizer_value is None
            else optimizer_value * (self.max - self.min) + self.min
        )


class Constraints(ModelConfig):
    phase: Annotated[Phase, Field(description="")]
    rate: Annotated[Tolerance, Field(description="")]
    duration: Annotated[Tolerance, Field(description="")]


# WellConstraintConfig = RootModel[Dict[str, Dict[int, Constraints]]]
class WellConstraintConfig(RootModelConfig):
    root: Dict[str, Dict[int, Constraints]]

    def __iter__(self) -> Iterator[str]:  # type: ignore
        return iter(self.root)

    @overload
    def get(self, __key: str) -> Dict[int, Constraints]:
        ...

    @overload
    def get(
        self, __key: str, __default: Dict[int, Constraints]
    ) -> Dict[int, Constraints]:
        ...

    def get(
        self, __key: str, __default: Optional[Dict[int, Constraints]] = None
    ) -> Optional[Dict[int, Constraints]]:
        if __default is None:
            return self.root.get(__key)
        return self.root.get(__key, __default)
