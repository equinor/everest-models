import datetime
import os
import pathlib
from textwrap import dedent
from typing import Any, Dict, List, Optional, Set, Tuple

from everest_models.jobs.shared.models import BaseConfig, BaseEnum


class ABEnum(BaseEnum):
    a = "A"
    b = "B"

    @classmethod
    def value_type(cls) -> Dict[str, Any]:
        return {"type": "string", "choices": [e.value for e in cls]}


class SubTester(BaseConfig):
    c: int = 53
    d: List[str]


class MainTester(BaseConfig):
    a: Optional[datetime.date]
    b: SubTester


class RootDictTester(BaseConfig):
    __root__: Dict[str, Dict[int, SubTester]]


class RootListTester(BaseConfig):
    __root__: Tuple[List[float], Set[SubTester]]


class EllipsisTester(BaseConfig):
    a: Tuple[int, ...]


class EnumTester(BaseConfig):
    x: ABEnum


def test_base_config_json_dump(tmpdir):
    class Tester(BaseConfig):
        path: pathlib.Path

    test_model = Tester(path="some/location.txt")
    output = pathlib.Path("output.json")
    cwd = pathlib.Path()
    tmpdir.chdir()
    test_model.json_dump(output)
    assert (
        output.read_bytes()
        == b"""{
  "path": "./some/location.txt"
}"""
    )
    test_model = Tester(path="/tmp/some/location.txt")
    test_model.json_dump(output)
    assert (
        output.read_bytes()
        == b"""{
  "path": "/tmp/some/location.txt"
}"""
    )
    os.chdir(cwd)


def test_base_config_help_schema_set_argument():
    schema = SubTester.help_schema()
    assert all(x not in ("fields", "arguments") for x in schema)
    schema = SubTester.help_schema("arg")
    assert schema["arguments"] == "arg"
    assert schema["fields"]
    args = ("arg1", "arg2")
    schema = SubTester.help_schema(args)
    assert isinstance(schema["arguments"], tuple)
    assert all(x in args for x in schema["arguments"])


def test_base_config_help_schema_enum():
    schema = EnumTester.help_schema()
    assert isinstance(schema, dict)
    assert isinstance(schema["x"], dict)
    assert all(x in ("type", "choices") for x in schema["x"])


def test_base_config_help_schema_ellipsis():
    schema = EllipsisTester.help_schema()
    assert isinstance(schema, dict)
    assert isinstance(schema["a"], list)


def test_base_config_help_schema():
    schema = MainTester.help_schema()
    assert isinstance(schema, dict)


def test_base_config_help_schema_list__root__():
    schema = RootListTester.help_schema()
    assert isinstance(schema, list)
    assert isinstance(schema[0], list)
    assert isinstance(schema[1], list)
    assert isinstance(schema[1][0], dict)
    assert isinstance(schema[1][0]["value"], dict)
    assert isinstance(schema[1][0]["value"]["d"], list)
    assert schema[1][0]["unique"] is True


def test_base_config_help_schema_dict__root__():
    schema = RootDictTester.help_schema()
    assert isinstance(schema, dict)
    assert isinstance(schema["string"], dict)
    assert isinstance(schema["string"]["integer"], dict)
    assert isinstance(schema["string"]["integer"]["d"], list)


def test_base_config_help_schema_yaml(capsys):
    MainTester.help_schema_yaml("args")
    out, _ = capsys.readouterr()
    assert out == dedent(
        """\
---
arguments: args
fields:
   a: {format: date, required: false, type: string}
   b:
      c: {default: 53, required: false, type: integer}
      d: [string]
...
"""
    )


def test_base_config_help_schema_yaml_list__root__(capsys):
    RootListTester.help_schema_yaml("args")
    out, _ = capsys.readouterr()
    assert out == dedent(
        """\
---
arguments: args
fields:
- [float]
- - unique: true
    value:
       c: {default: 53, required: false, type: integer}
       d: [string]
...
"""
    )


def test_base_config_help_schema_yaml_dict__root__(capsys):
    RootDictTester.help_schema_yaml("args")
    out, _ = capsys.readouterr()
    assert out == dedent(
        """\
---
arguments: args
fields:
   string:
      integer:
         c: {default: 53, required: false, type: integer}
         d: [string]
...
"""
    )
