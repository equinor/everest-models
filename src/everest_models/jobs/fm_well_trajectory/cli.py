import logging
from pathlib import Path

from .outputs import write_guide_points, write_mlt_guide_md, write_mlt_guide_points
from .parser import build_argument_parser
from .read_trajectories import read_trajectories
from .well_trajectory_resinsight import well_trajectory_resinsight
from .well_trajectory_simple import well_trajectory_simple

logger = logging.getLogger(__name__)

FULL_JOB_NAME = "Well trajectory"


def main_entry_point(args=None):
    args_parser = build_argument_parser()
    options = args_parser.parse_args(args)

    if options.lint:
        args_parser.exit()

    guide_points = read_trajectories(
        options.config.scales,
        options.config.references,
        options.config.wells,
        options.config.platforms,
    )
    logger.info("Writing guide points to 'guide_points.json'")
    write_guide_points(guide_points, Path("guide_points.json"))

    if options.config.interpolation.type == "simple":
        well_trajectory_simple(
            options.config.wells,
            options.config.interpolation,
            options.config.npv_input_file,
            guide_points,
        )

    if options.config.connections:
        if (
            eclipse_model := options.eclipse_model or options.config.eclipse_model
        ) is None:
            args_parser.error("missing eclipse model")
        mlt_guide_points = well_trajectory_resinsight(
            options.config, eclipse_model, guide_points
        )
        if mlt_guide_points:
            logger.info("Writing multilateral guide points to 'mlt_guide_points.json'")
            write_mlt_guide_points(mlt_guide_points, Path("mlt_guide_points.json"))
            logger.info("Writing multilateral guide md's to 'mlt_guide_md.json'")
            write_mlt_guide_md(mlt_guide_points, Path("mlt_guide_md.json"))
