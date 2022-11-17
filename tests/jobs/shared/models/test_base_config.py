import datetime
import os
import pathlib
from typing import List, Optional, Tuple

from spinningjenny.jobs.shared.models import BaseConfig


class SubTester(BaseConfig):
    c: int = 53
    d: List[str]


class MainTester(BaseConfig):
    a: Optional[datetime.date]
    b: SubTester


class RootTester(BaseConfig):
    __root__: Tuple[SubTester, ...]


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


def test_base_config_help_schema():
    schema = MainTester.help_schema()
    assert isinstance(schema, dict)
    assert not any(x in ("fields", "argument") for x in schema)
    assert MainTester.help_schema("args") == {
        "argument": "args",
        "fields": {
            "a": {"required": False, "type": "string", "format": "date"},
            "b": {
                "c": {"required": False, "type": "integer", "default": 53},
                "d": ["string"],
            },
        },
    }


def test_base_config_help_schema__root__():
    schema = RootTester.help_schema()
    assert isinstance(schema, list)

    schema = RootTester.help_schema("arg")
    assert schema.get("argument") == "arg"
    assert isinstance(schema.get("fields"), list)


def test_base_config_help_schema_yaml(capsys):
    MainTester.help_schema_yaml("args")
    out, _ = capsys.readouterr()
    assert (
        out
        == """argument: args
fields:
   a: {format: date, required: false, type: string}
   b:
      c: {default: 53, required: false, type: integer}
      d: [string]
"""
    )


def test_base_config_help_schema_yaml__root__(capsys):
    RootTester.help_schema_yaml("args")
    out, _ = capsys.readouterr()
    assert (
        out
        == """argument: args
fields:
- c: {default: 53, required: false, type: integer}
  d: [string]
"""
    )
