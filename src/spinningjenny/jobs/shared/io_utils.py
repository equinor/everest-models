import json

import ruamel.yaml as yaml


def write_json_to_file(dictionary, file_name):
    with open(file_name, "w") as outfile:
        json.dump(dictionary, outfile, indent=2, separators=(",", ": "))


def write_yaml_to_file(dictionary, file_name):
    with open(file_name, "w") as outfile:
        _yaml = yaml.YAML(typ="safe", pure=True)
        _yaml.default_flow_style = False
        _yaml.dump(dictionary, outfile)


def load_yaml(file_path):
    with open(file_path, "r") as input_file:
        input_data = input_file.readlines()
        try:
            loaded_yaml = yaml.YAML(typ="safe", pure=True).load("".join(input_data))
            return loaded_yaml
        except yaml.YAMLError as exc:
            if hasattr(exc, "problem_mark"):
                # this code block is never tested
                mark = exc.problem_mark
                raise yaml.YAMLError(
                    str(exc)
                    + "\nError in line: {}\n {}^)".format(
                        input_data[mark.line], " " * mark.column
                    )
                )
