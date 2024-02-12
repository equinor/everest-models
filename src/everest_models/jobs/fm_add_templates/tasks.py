import itertools
import logging
import pathlib
from typing import Iterator, Sequence, Tuple

from everest_models.jobs.shared.converters import path_to_str
from everest_models.jobs.shared.models import Operation, Well

from .config_model import Template

logger = logging.getLogger(__name__)


def collect_matching(
    templates: Sequence[Template], wells: Sequence[Well]
) -> Iterator[Tuple[str, Operation, Template]]:
    """Collect data from template and well model, where template's keys and well's operation match.

    Args:
        templates (TemplateConfig): template configuration model
        wells (Wells): well model

    Yields:
        Iterator[Tuple[str, Operation, TemplateConfig]]: well name, matching well operations and template
    """
    for well in wells:
        for operation, template in (
            (x, y)
            for x, y in itertools.product(well.operations, templates)
            if y.matching_keys(x)
        ):
            yield well.name, operation, template


def add_templates(
    well_name: str, operation: Operation, template: Template
) -> pathlib.Path:
    """Set well operation template variable to template filepath.

    Mark template as used.

    Args:
        well_name (str): well name
        operation (Operation): well operation
        template (Template): template configuration
    """
    operation.template = template.file
    logger.info(
        f"Template '{path_to_str(template.file)}' was inserted for "
        f"well '{well_name}' date '{operation.date}' operation '{operation.opname}'"
    )
    return template.file


def insert_template_with_matching_well_operation(
    templates: Sequence[Template], wells: Sequence[Well]
) -> Iterator[pathlib.Path]:
    return (
        add_templates(well_name, operation, template)
        for well_name, operation, template in collect_matching(templates, wells)
        if not operation.template
    )
