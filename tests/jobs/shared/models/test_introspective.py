from enum import Enum
from io import StringIO
from textwrap import dedent
from typing import Any, List, Optional, Sequence, Set, Tuple, Type, Union

import pytest
from everest_models.jobs.shared.models.base_config.introspective import (
    CommentedObject,
    build_yaml_structure,
    builtin_datatypes,
)
from hypothesis import given
from hypothesis.strategies import booleans, floats, integers, text
from pydantic import BaseModel
from ruamel.yaml import YAML


@pytest.fixture(scope="package")
def yaml() -> YAML:
    _yaml = YAML()
    _yaml.indent(mapping=2, sequence=2, offset=0)
    return _yaml


@pytest.mark.parametrize(
    "data, expected",
    (
        pytest.param(
            {"key": CommentedObject("value", "Top level comment", "Inline comment")},
            dedent(
                """\
                # Top level comment
                key: value  # Inline comment
                """
            ),
            id="simple mapping",
        ),
        pytest.param(
            {
                "nested": CommentedObject(
                    {"inner_key": CommentedObject("inner_value", "Inner comment")},
                    "Nested comment",
                )
            },
            dedent(
                """\
                # Nested comment
                nested:
                  # Inner comment
                  inner_key: inner_value
                """
            ),
            id="nested mapping",
        ),
        pytest.param(
            [
                CommentedObject(1, inline_comment="First item"),
                CommentedObject(2, "Second item"),
            ],
            dedent(
                """\
                - 1  # First item
                - 2
                """
            ),
            id="sequence",
        ),
        pytest.param(
            {"list": CommentedObject([{"dict_in_list": True}], "List item comment")},
            dedent(
                """\
                # List item comment
                list:
                - dict_in_list: true
                """
            ),
            id="mixed data",
        ),
        pytest.param(
            {
                "list": CommentedObject(
                    [
                        {
                            "string_a": [True, False],
                            "string_b": CommentedObject(
                                {"string_x": 0.5},
                                "string_b comment",
                                "TODO: I will not do it",
                            ),
                        }
                    ],
                    "List item comment",
                )
            },
            dedent(
                """\
                # List item comment
                list:
                - string_a:
                  - true
                  - false
                    # string_b comment
                  string_b:  # TODO: I will not do it
                    string_x: 0.5
                """
            ),
            id="deeply nested",
        ),
    ),
)
def test_build_yaml_structure(data: Any, expected: str, yaml: YAML):
    io = StringIO()
    yaml.dump(build_yaml_structure(data), io)
    assert io.getvalue() == expected


@given(integers())
def test_builtin_datatypes_with_integers(value):
    assert builtin_datatypes(value) == "integer"


@given(text())
def test_builtin_datatypes_with_strings(value):
    assert builtin_datatypes(value) == "string"


@given(booleans())
def test_builtin_datatypes_with_booleans(value):
    assert builtin_datatypes(value) == "boolean"


@given(floats())
def test_builtin_datatypes_with_floats(value):
    assert builtin_datatypes(value) == "number"


def test_builtin_datatypes_with_base_model():
    class MyModel(BaseModel):
        pass

    assert builtin_datatypes(MyModel) == "MyModel map"


def test_builtin_datatypes_with_enum():
    class MyEnum(Enum):
        A = 1
        B = 2

    assert builtin_datatypes(MyEnum) == "integer"
    assert builtin_datatypes(MyEnum.B) == "integer"


@pytest.mark.parametrize(
    "typ, expected",
    (
        pytest.param(Sequence[int], "[integer]", id="sequence"),
        pytest.param(Union[int, float], "integer or number", id="union"),
        pytest.param(Optional[int], "integer", id="optional"),
        pytest.param(Set[int], "unique values [integer]", id="set"),
        pytest.param(List[str], "[string]", id="list"),
        pytest.param(Tuple[int, int], "[integer, integer]", id="tuple"),
    ),
)
def test_builtin_datatypes_with_sequence(typ: Type, expected: str):
    assert builtin_datatypes(typ) == expected
