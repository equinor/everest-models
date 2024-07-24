import json
import linecache
from pathlib import Path
from typing import Any, Optional, TextIO, Union

import ruamel.yaml as yaml


def load_json(path: Union[Path, str]):
    with Path(path).open("r", encoding="utf-8") as fd:
        return json.load(fd)


def load_yaml(path: Union[Path, str]):
    path = Path(path)
    try:
        return yaml.YAML(typ="safe", pure=True).load(path.read_bytes())
    except yaml.YAMLError as ye:
        if mark := getattr(ye, "problem_mark", None):
            raise yaml.YAMLError(
                f"Error in file '{path}' (line {mark.line + 1}):"
                f"\n\t{linecache.getline(str(path), mark.line + 1)}"
                f"\t{' ' * mark.column}^"
            ) from ye
        raise yaml.YAMLError(str(ye)) from ye


def load_supported_file_encoding(path: Path) -> Any:
    if (
        loader := {
            ".json": load_json,
            ".yaml": load_yaml,
            ".yml": load_yaml,
        }.get(path.suffix)
    ) is None:
        raise ValueError(f"Unsupported file encoding:\n\t{path.absolute()}")
    return loader(path)


def dump_json(data: dict, path: Path):
    with path.open("w") as fd:
        json.dump(data, fd, indent=2, separators=(",", ": "), sort_keys=True)


def dump_yaml(
    data: dict,
    fp: TextIO,
    explicit: bool = False,
    default_flow_style: Optional[bool] = None,
):
    _yaml = yaml.YAML()
    _yaml.default_flow_style = default_flow_style
    _yaml.explicit_start = explicit
    _yaml.explicit_end = explicit
    _yaml.representer.add_representer(
        type(None), lambda x, _: x.represent_scalar("tag:yaml.org,2002:null", "null")
    )
    _yaml.indent(mapping=2, sequence=4, offset=2)
    _yaml.dump(data, fp)
