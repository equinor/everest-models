from typing import Any, Dict, Union

from pydantic import BaseModel, ConfigDict, RootModel, ValidationInfo, field_validator
from pydantic_core import PydanticUndefined
from ruamel.yaml.comments import CommentedMap, CommentedSeq
from typing_extensions import override

from .introspective import build_yaml_structure, parse_annotation, parse_field_info

__all__ = ["ModelConfig", "RootModelConfig"]


class ModelConfig(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        frozen=True,
        extra="forbid",
        ser_json_timedelta="iso8601",
        regex_engine="rust-regex",
    )

    @field_validator("*", mode="before")
    @classmethod
    def check_for_ellipses(cls, value: Any, info: ValidationInfo) -> Any:
        if value == "...":
            if (
                default := info.field_name and cls.model_fields[info.field_name].default
            ) is PydanticUndefined:
                raise ValueError("Please replace `...`, this field is required")
            return default
        return value

    @classmethod
    def introspective_data(cls) -> Dict[str, Any]:
        return {
            field: parse_field_info(info) for field, info in cls.model_fields.items()
        }

    @classmethod
    def commented_map(cls) -> Union[CommentedMap, CommentedSeq]:
        return build_yaml_structure(cls.introspective_data())


class RootModelConfig(ModelConfig, RootModel):
    model_config = ConfigDict(extra=None)

    @override
    @classmethod
    def introspective_data(cls) -> Any:
        return parse_annotation(cls.model_fields["root"].annotation)
