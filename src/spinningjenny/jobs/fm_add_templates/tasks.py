import itertools
import logging
from typing import Iterator, Tuple

from spinningjenny.jobs.fm_add_templates.template_model import Template, TemplateConfig
from spinningjenny.jobs.shared.converters import path_to_str
from spinningjenny.jobs.shared.models import Operation, WellListModel

logger = logging.getLogger(__name__)


def collect_matching(
    templates: TemplateConfig, wells: WellListModel
) -> Iterator[Tuple[str, Operation, TemplateConfig]]:
    """Collect data from template and well model, where template's keys and well's operation match.

    Args:
        templates (TemplateConfig): template configuration model
        wells (WellListModel): well model

    Yields:
        Iterator[Tuple[str, Operation, TemplateConfig]]: well name, matching well operations and template
    """
    for well in wells:
        for op, template in (
            (x, y) for x, y in itertools.product(well.ops, templates) if y.keys == x
        ):
            yield well.name, op, template


def add_templates(well_name: str, operation: Operation, template: Template) -> None:
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
    template.is_utilized = True
