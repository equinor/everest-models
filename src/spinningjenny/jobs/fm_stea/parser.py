import argparse
from functools import partial

from spinningjenny.jobs.shared.validators import valid_file


def build_argument_parser():
    description = (
        "STEA is a powerful economic analysis tool used for complex economic "
        "analysis and portfolio optimization. STEA helps you analyze single "
        "projects, large and small portfolios and complex decision trees. "
        "As output, for each of the entries in the result section of the "
        "yaml config file, STEA will create result files "
        "ex: Res1_0, Res2_0, .. Res#_0"
    )
    parser = argparse.ArgumentParser(description=description)

    parser.add_argument(
        "-c",
        "--config",
        type=partial(valid_file, parser=parser),
        help="STEA config file, yaml format required",
        required=True,
    )
    return parser


args_parser = build_argument_parser()
