from pathlib import Path

from ruamel.yaml import YAML
from ruamel.yaml.error import YAMLError

from everest_models.jobs.shared.resinsight import ResInsight

from .config_model import DistanceConfig
from .parser import build_argument_parser
from .tasks import run


def load_config(config_path: Path) -> DistanceConfig:
    yaml = YAML(typ="safe")
    yaml.allow_duplicate_keys = False
    with config_path.open(encoding="utf-8") as config_file:
        return DistanceConfig.model_validate(yaml.load(config_file))


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
