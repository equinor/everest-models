from typing import Any, Dict, Union

from pydantic import (
    BaseModel,
    ConfigDict,
    RootModel,
    model_validator,
)
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

    @model_validator(mode="before")
    @classmethod
    def check_for_ellipses(cls, data: Any) -> Any:
        def any_ellipses(data: Any):
            return any(
                any_ellipses(value) if isinstance(value, dict) else value == "..."
                for value in (data.values() if isinstance(data, dict) else data)
            )

        if any_ellipses(data):
            raise ValueError(
                "Please replace any and/or all `...`, these field are required"
            )
        return data

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
