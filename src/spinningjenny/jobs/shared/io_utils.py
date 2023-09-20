import json
import linecache
from pathlib import Path
from typing import TextIO

import ruamel.yaml as yaml


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as fd:
        return json.load(fd)


def load_yaml(path: Path):
    try:
        return yaml.YAML(typ="safe", pure=True).load(path.read_bytes())
    except yaml.YAMLError as ye:
        if mark := getattr(ye, "problem_mark", None):
            raise yaml.YAMLError(
                f"Error in file '{path}' (line {mark.line + 1}):"
                f"\n\t{linecache.getline(str(path), mark.line + 1)}"
                f"\t{' ' * mark.column}^"
            ) from ye
        else:
            raise yaml.YAMLError(str(ye)) from ye


def dump_json(data: dict, path: Path):
    with path.open("w") as fd:
        json.dump(data, fd, indent=2, separators=(",", ": "), sort_keys=True)


def dump_yaml(
    data: dict, fp: TextIO, explicit: bool = False, default_flow_style: bool = None
):
    _yaml = yaml.YAML(typ="safe", pure=True)
    if default_flow_style is not None:
        _yaml.default_flow_style = default_flow_style
    _yaml.explicit_start = explicit
    _yaml.explicit_end = explicit
    _yaml.indent(mapping=3, sequence=2, offset=0)
    _yaml.dump(data, fp)
