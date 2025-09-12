import collections
import logging
from typing import Iterable

from everest_models.jobs.shared.converters import path_to_str
from everest_models.jobs.shared.models import Well

from .config_model import Template
from .parser import build_argument_parser
from .tasks import insert_template_with_matching_well_operation

logger = logging.getLogger(__name__)

FULL_JOB_NAME = "Add templates"


def _duplicate_template_msg(templates: Iterable[Template]) -> str:
    return "\n".join(
        f"Found duplicate template file path {path_to_str(path)} in config file!"
        for path, count in collections.Counter(
            entry.file for entry in templates
        ).items()
        if count > 1
    )


def _no_template_msg(wells: Iterable[Well]) -> str:
    string = []
    for well in wells:
        if sub_str := "\n".join(
            f"\toperation: {name}\tdate: {date}"
            for name, date in well.missing_templates
        ):
            string.append(f"Well: {well.name}\n{sub_str}")
    return "\n".join(string)


def main_entry_point(args=None):
    args_parser = build_argument_parser()
    options = args_parser.parse_args(args)
    if msg := _duplicate_template_msg(options.config.templates):
        logger.warning(msg)

    if options.input and options.config.wells:
        args_parser.error("--input and config.wells are mutually exclusive!")

    if not options.input and not options.config.wells:
        args_parser.error("either --input or config.wells must be provided!")

    if options.lint:
        args_parser.exit()

    wells = options.input or options.config.wells

    consumed_templates = insert_template_with_matching_well_operation(
        options.config.templates, wells
    )

    if unutilized := ", ".join(
        map(
            path_to_str,
            {template.file for template in options.config.templates}
            - set(consumed_templates),
        )
    ):
        logger.warning(
            f"Template(s) not inserted:\n\t{unutilized}\n\tPlease, check insertion keys!"
        )

    if msg := _no_template_msg(wells):
        args_parser.error("No template matched:\n" + msg)

    wells.json_dump(options.output)
