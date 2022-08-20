import json
import logging

import ruamel.yaml as yaml

logger = logging.getLogger(__name__)


def interpret_well_drill(dakota_values_file, output_file):
    with open(dakota_values_file, "r") as f:
        dakota_yaml = yaml.YAML(typ="safe", pure=True).load(f)

    wells_to_keep = [well for well, value in dakota_yaml.items() if value >= 0.5]

    with open(output_file, "w") as f:
        f.write(json.dumps(wells_to_keep))

    return wells_to_keep
