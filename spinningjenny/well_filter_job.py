import json

from spinningjenny import customized_logger

logger = customized_logger.get_logger(__name__)


def filter_wells(wells_file, output_file, keep_file=None, remove_file=None):
    with open(wells_file, "r") as f:
        wells = json.load(f)

    if keep_file and remove_file:
        raise ValueError(
            "well_filter requires either the --keep or --remove flag to be set, not both"
        )
    if not (keep_file or remove_file):
        raise ValueError(
            "well_filter requires either the --keep or --remove flag to be set"
        )

    if keep_file:
        with open(keep_file, "r") as f:
            keep_wells = json.load(f)
    else:
        with open(remove_file, "r") as f:
            remove_wells = json.load(f)
        keep_wells = [
            well["name"] for well in wells if well["name"] not in remove_wells
        ]

    filtered_wells = [well for well in wells if well["name"] in keep_wells]

    with open(output_file, "w") as f:
        f.write(json.dumps(filtered_wells))

    return filtered_wells
