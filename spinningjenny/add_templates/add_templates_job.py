import copy
import logging
import sys
from collections import Counter, namedtuple

Template = namedtuple("Template", ("file", "key_set"))
logger = logging.getLogger(__name__)


def add_templates(templates, wells):
    """Insert a template file path for each well operation where the template
    keys match the operation details. Also return any template paths that were
    not inserted due to unmatched keys.
    """
    wells = copy.deepcopy(wells)
    warnings = []
    errors = []
    used_templates = set([])

    processed_templates = sorted(
        (
            Template(
                file=entry.file,
                key_set=set([(elem.key, elem.value) for elem in entry.keys]),
            )
            for entry in templates
        ),
        key=lambda tmp: len(tmp.key_set),
    )

    msg = "Template '{}' was inserted for well '{}' date '{}' operation '{}'"
    for well in wells:
        # Get the operations associated with the well
        well_name = well.get("name", "")
        for op in well.get("ops", []):
            op_name = op.get("opname", "")
            op_date = op.get("date", "")
            for entry in processed_templates:
                if entry.key_set.issubset(set(op.items())):
                    op["template"] = entry.file
                    logger.info(msg.format(entry.file, well_name, op_date, op_name))
                    used_templates.add(entry.file)

            if "template" not in op:
                errors.append(
                    "No template matched for well:'{w}' operation:'{o}' at date:'{d}'".format(
                        w=well_name, o=op_name, d=op_date
                    )
                )

    template_paths = set([entry.file for entry in templates])
    unused_templates = template_paths.difference(used_templates)
    for entry in unused_templates:
        warnings.append(
            "Template {} was not inserted, check insertion keys!".format(entry)
        )

    return wells, warnings, errors


def find_template_duplicates(templates):
    """Returns a list file paths that are duplicate"""
    counted = Counter([entry.file for entry in templates])
    return [path for path in counted if counted[path] > 1]
