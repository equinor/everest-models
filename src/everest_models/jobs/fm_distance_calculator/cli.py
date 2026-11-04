from pathlib import Path
from typing import Any

from ruamel.yaml import YAML
from ruamel.yaml.error import YAMLError

from everest_models.jobs.shared.resinsight import ResInsight

from .parser import build_argument_parser
from .tasks import normalize_config, run


def _validate_hyphenated_keys(value: Any) -> None:
    if isinstance(value, dict):
        for key, nested_value in value.items():
            if isinstance(key, str) and "_" in key:
                raise ValueError(
                    f"Config key '{key}' must use hyphens instead of underscores."
                )
            _validate_hyphenated_keys(nested_value)
    elif isinstance(value, list):
        for nested_value in value:
            _validate_hyphenated_keys(nested_value)


def load_config(config_path: Path) -> dict[str, Any]:
    yaml = YAML(typ="safe")
    yaml.allow_duplicate_keys = False
    with config_path.open(encoding="utf-8") as config_file:
        config = yaml.load(config_file) or {}
    if not isinstance(config, dict):
        raise ValueError("Top-level YAML must be a mapping")
    _validate_hyphenated_keys(config)
    config = normalize_config(config)
    calculations = config.get("distance_calculations")
    if not isinstance(calculations, list) or not calculations:
        raise ValueError("No 'distance_calculations' entries found in the YAML config.")
    return config


def main_entry_point(args=None) -> int:
    parser = build_argument_parser()
    options = parser.parse_args(args)
    try:
        config = load_config(options.config)
    except (OSError, ValueError, YAMLError) as error:
        parser.error(str(error))

    if options.lint:
        parser.exit()

    if options.egrid is None and options.case_name is None:
        parser.error("Provide --case_name or --egrid")
    egrid_path = (
        options.egrid
        if options.egrid is not None
        else Path(f"{options.case_name}.EGRID")
    ).resolve()
    if not egrid_path.is_file():
        parser.error(f"EGRID not found: {egrid_path}")

    with ResInsight(options.resinsight) as instance:
        case = instance.project.load_case(str(egrid_path))
        if case is None:
            raise RuntimeError(f"ResInsight could not load case: {egrid_path}")
        return run(config, case)
