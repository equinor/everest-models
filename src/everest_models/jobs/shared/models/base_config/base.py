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
    """
    Introspective pydantic 2 BaseModel.

    Use for any model that you wish to expose the model's specification to a user.

    NOTE: If your not planning to access your model fields introspectivally
    please stick to pydantic BaseModel. This base model can be expensive

    Attributes:
    - model_config:
      - str_strip_whitespace = True
      - frozen = True
      - extra = "forbid"
      - ser_json_timedelta = "iso8601"
      - regex_engine = "rust-regex"

    Methods:
    - introspective_data() -> Dict[str, Any]: Returns introspective data about the
      models fields.
    - commented_map() -> Union[CommentedMap, CommentedSeq]: Returns a commented map
      or sequence based on the introspective data.

    Raises:
    - ValueError: If a field's value is set to '...'  and the field is required and has no default.

    Usage:
    class MyModel(ModelConfig):
        some_field: int

    data = MyModel.introspective_data()
    map = MyModel.commented_map()
    """

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
    def introspective_data(
        cls, minimal: bool, no_comment: bool = False
    ) -> Dict[str, Any]:
        """
        Returns introspective data about the model fields.

        This method returns a dictionary containing information about each field in the
        model. The keys of the dictionary are the field names, and the values are
        dictionaries containing information about each field.

        Args:
            minimal (bool): process only required fields
            no_comment (bool): skip comment build process
        Returns:
            Dict[str, Any]: A dictionary containing introspective data about the model
            fields. Where Any is a nested CommentedObject

        Raises:
            None

        Example:
            {
                'field1': CommentedObject(
                    value=5,
                    comment='comment containing introspective information on value',
                    inline_comment=None
                ),
                'field2': CommentedObject(
                    value={
                        'field2_a': CommentedObject(
                            value='...',
                            comment='more comment',
                            inline_comment='replace value'
                        ),
                    },
                    comment='comment containing introspective information on value',
                    inline_comment=None
                ),
                ...
            }
        """
        model_fields = (
            filter(lambda data: data[1].is_required(), cls.model_fields.items())
            if minimal
            else cls.model_fields.items()
        )
        return {
            field: parse_field_info(info, minimal, no_comment)
            for field, info in model_fields
        }

    @classmethod
    def commented_map(cls, minimal: bool) -> Union[CommentedMap, CommentedSeq]:
        """
        Recursively go through model fields and build an comment injected yaml object.

        where key is the field in the model
        value is the default value of the field or `...`
        and injected comment is the introspective information on the field and value

        Args:
            minimal (bool): process only required fields

        Returns:
        Union[CommentedMap, CommentedSeq]: A CommentedMap or CommentedSeq object based
        on the introspective data.
        """
        return build_yaml_structure(cls.introspective_data(minimal))


class RootModelConfig(ModelConfig, RootModel):
    """
    Same as ModelConfig but for RootModel
    """

    model_config = ConfigDict(extra=None)

    @override
    @classmethod
    def introspective_data(cls, minimal: bool, no_comment: bool = False) -> Any:
        return parse_annotation(
            cls.model_fields["root"].annotation, minimal, no_comment
        )
