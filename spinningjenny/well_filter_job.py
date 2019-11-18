import json

from spinningjenny import customized_logger

logger = customized_logger.get_logger(__name__)


def filter_wells(wells, parser, keep_wells=None, remove_wells=None):
    if keep_wells and remove_wells:
        parser.error(
            "well_filter requires either the --keep or --remove flag to be set, not both"
        )
    if keep_wells is None and remove_wells is None:
        parser.error(
            "well_filter requires either the --keep or --remove flag to be set"
        )
    elif remove_wells is not None:
        return [well for well in wells if well["name"] not in remove_wells]

    elif keep_wells is not None:
        return [well for well in wells if well["name"] in keep_wells]


def write_results(wells, output):
    with open(output, "w") as f:
        f.write(json.dumps(wells))
