from enum import Enum
from io import StringIO
from textwrap import dedent
from typing import Any, Dict, Tuple

import pytest
from everest_models.jobs.shared.models import ModelConfig, RootModelConfig
from pydantic import Field, FilePath, ValidationError
from ruamel.yaml import YAML
from typing_extensions import Annotated


class Sex(Enum):
    MALE = "male"
    FEMALE = "female"


class User(ModelConfig):
    name: Annotated[str, Field("some_name", description="The name of the test model")]
    age: Annotated[
        int, Field(description="Long live the test model", examples=[5, "1.5e4"])
    ]
    sex: Annotated[Sex, Field(Sex.MALE, description="Sex of the user")]


class UserSequence(RootModelConfig):
    root: Tuple[User, ...]


class DeepNested(RootModelConfig):
    root: Dict[str, Dict[int, User]]


class Wrapper(ModelConfig):
    user: Annotated[
        User, Field(description="User description. A relatively simple data.")
    ]
    user_id: int = 213
    data: FilePath


@pytest.mark.parametrize(
    "model, expected",
    (
        pytest.param(
            Wrapper,
            dedent(
                """
                # User description. A relatively simple data.
                # Datatype: User map
                # Required: True
                user:

                  # The name of the test model
                  # Datatype: string
                  # Examples: a string value
                  # Required: False
                  # Default: some_name
                  name: some_name

                  # Long live the test model
                  # Datatype: integer
                  # Examples: 5, 1.5e4
                  # Required: True
                  age: '...'  # ← REPLACE

                  # Sex of the user
                  # Datatype: string
                  # Choices: male, female
                  # Required: False
                  # Default: male
                  sex: male

                # Datatype: integer
                # Examples: 1, 1.34E5, 1.34e5
                # Required: False
                # Default: 213
                user_id: 213

                # Datatype: Path
                # Examples: /path/to/file.ext, /path/to/dirictory/
                # Required: True
                data: '...'  # ← REPLACE
                """
            ),
            id="wrapper over user",
        ),
        pytest.param(
            UserSequence,
            dedent(
                """\
                -

                  # The name of the test model
                  # Datatype: string
                  # Examples: a string value
                  # Required: False
                  # Default: some_name
                  name: some_name

                  # Long live the test model
                  # Datatype: integer
                  # Examples: 5, 1.5e4
                  # Required: True
                  age: '...'  # ← REPLACE

                  # Sex of the user
                  # Datatype: string
                  # Choices: male, female
                  # Required: False
                  # Default: male
                  sex: male
                """
            ),
            id="sequence of users",
        ),
        pytest.param(
            DeepNested,
            dedent(
                """\
                <string>:
                  <integer>:

                    # The name of the test model
                    # Datatype: string
                    # Examples: a string value
                    # Required: False
                    # Default: some_name
                    name: some_name

                    # Long live the test model
                    # Datatype: integer
                    # Examples: 5, 1.5e4
                    # Required: True
                    age: '...'  # ← REPLACE

                    # Sex of the user
                    # Datatype: string
                    # Choices: male, female
                    # Required: False
                    # Default: male
                    sex: male
                """
            ),
            id="deeply nested user",
        ),
    ),
)
def test_base_config_commented_map(model: ModelConfig, expected: str) -> None:
    map = model.commented_map()
    collector = StringIO()
    YAML().dump(map, collector)
    assert collector.getvalue() == expected


def test_base_config_check_for_ellipses() -> None:
    with pytest.raises(ValidationError, match="Field required"):
        User.model_validate({})
    with pytest.raises(
        ValidationError,
        match="Please replace any and/or all `...`, these field are required",
    ):
        User.model_validate({"age": "..."})


@pytest.mark.parametrize(
    "model, expected",
    (
        pytest.param(
            Wrapper,
            {
                "str_strip_whitespace": True,
                "frozen": True,
                "extra": "forbid",
                "ser_json_timedelta": "iso8601",
                "regex_engine": "rust-regex",
            },
            id="ModelConfig",
        ),
        pytest.param(
            DeepNested,
            {
                "str_strip_whitespace": True,
                "frozen": True,
                "extra": None,
                "ser_json_timedelta": "iso8601",
                "regex_engine": "rust-regex",
            },
            id="RootModelConfig",
        ),
    ),
)
def test_base_config_model(model: ModelConfig, expected: Dict[str, Any]) -> None:
    assert model.model_config == expected
