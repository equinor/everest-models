#!/usr/bin/env python
import collections
import logging

from spinningjenny.jobs.fm_add_templates import tasks
from spinningjenny.jobs.fm_add_templates.config_model import TemplateConfig
from spinningjenny.jobs.fm_add_templates.parser import build_argument_parser
from spinningjenny.jobs.shared.converters import path_to_str
from spinningjenny.jobs.shared.models import WellConfig

logger = logging.getLogger(__name__)


def _duplicate_template_msg(templates: TemplateConfig) -> str:
    return "\n".join(
        f"Found duplicate template file path {path_to_str(path)} in config file!"
        for path, count in collections.Counter(
            entry.file for entry in templates
        ).items()
        if count > 1
    )


def _no_template_msg(wells: WellConfig) -> str:
    string = []
    for well in wells:
        if sub_str := "\n".join(
            "\t" f"operation: {opname}" "\t" f"date: {date}"
            for opname, date in well.missing_templates()
        ):
            string.append(f"Well: {well.name}\n{sub_str}")
    return "\n".join(string)


def main_entry_point(args=None):
    args_parser = build_argument_parser()
    options = args_parser.parse_args(args)
    if msg := _duplicate_template_msg(options.config.templates):
        logger.warning(msg)

    if options.lint:
        args_parser.exit()

    consumed_templates = tasks.insert_template_with_matching_well_operation(
        options.config.templates, options.input
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

    if msg := _no_template_msg(options.input):
        args_parser.error("No template matched:\n" + msg)

    options.input.json_dump(options.output)


if __name__ == "__main__":
    main_entry_point()
