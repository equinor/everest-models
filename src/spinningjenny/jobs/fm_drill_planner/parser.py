from functools import partial

from spinningjenny.jobs.fm_drill_planner.models import DrillPlanConfig, Optimizer, Wells
from spinningjenny.jobs.shared.arguments import (
    SchemaAction,
    add_output_argument,
    add_wells_input_argument,
    bootstrap_parser,
)
from spinningjenny.jobs.shared.models.wells import WellListModel
from spinningjenny.jobs.shared.validators import parse_file, valid_input_file

_CONFIG_ARGUMENT = "-c/--config"
SCHEMAS = {
    "config": DrillPlanConfig,
    "optimizer": Optimizer,
    "input": WellListModel,
}


def build_argument_parser():
    SchemaAction.register_models(
        {_CONFIG_ARGUMENT: DrillPlanConfig, "-opt/--optimizer": Optimizer}
    )
    parser, required_group = bootstrap_parser(
        description="A module that given a well priority list and a set of constraints, "
        "creates a list of dates for each well to be completed. "
        "Any well may have multiple options as to where it can be drilled, "
        "both for different slots and rigs. The module will try to find the "
        "optimum event combinations that allows for the wells to be completed "
        "as quickly as possible, and at the same time make sure that the "
        "dates that are output will be a valid drill plan."
    )
    add_wells_input_argument(
        required_group,
        help="File containing information related to wells. The format is "
        "consistent with the wells.json file when running everest and can "
        "be used directly.",
        schema=Wells,
    )
    add_output_argument(
        required_group,
        help="Name of the output-file. The output-file (json) will contain the same "
        "information as the input-file, including the results from the "
        "drill_planner. Please note that it is highly recommended to not use the "
        "same filename as the input-file. In cases where the same workflow is run "
        "twice, it is generally advised that the input-file for each job is consistent",
    )
    required_group.add_argument(
        *_CONFIG_ARGUMENT.split("/"),
        required=True,
        type=partial(parse_file, schema=DrillPlanConfig),
        help="Configuration file in yaml format describing the constraints of the field "
        "development. The file must contain information about rigs and slots "
        "that the wells can be drilled through. Additional information, such as "
        "when rigs and slots are available is also added here.",
    )
    required_group.add_argument(
        "-opt",
        "--optimizer",
        required=True,
        type=valid_input_file,
        help="The optimizer file in yaml format is the file output from everest that "
        "contains the well priority values - a float for each well.",
    )
    parser.add_argument(
        "-tl",
        "--time-limit",
        type=int,
        default=3600,
        help="Maximum time limit for the solver in seconds."
        "If a solution has not been reached within this time, a greedy"
        "approach will be used instead.",
    )
    parser.add_argument(
        "--ignore-end-date",
        action="store_true",
        help="Ignore the end date in the config file.",
    )
    return parser
