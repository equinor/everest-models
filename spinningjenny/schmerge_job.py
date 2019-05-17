import os
import re
import json
from collections import defaultdict, OrderedDict
from datetime import datetime
from jinja2 import Template
from spinningjenny import customized_logger

logger = customized_logger.get_logger(__name__)

COMMENT_INDICATOR = "--"
PLACEHOLDER_INDICATOR = "<<{}>>"
INSERT_SCHEDULE_DATE = "DATES{l} {{}} / --ADDED{l}/{l}{l}".format(l=os.linesep)

COMMENT_IGNORING_LINESEP = "{l}(?:--.*{l}|)*".format(l=os.linesep)
FIND_DATE_REGEX = "DATES{c} {{}} /{c}/{c}{l}".format(
    c=".*" + COMMENT_IGNORING_LINESEP, l=COMMENT_IGNORING_LINESEP
)

LOG_AFTER_END_NOTIFICATION = ", this occurs after the END keyword"


def _get_line_number_and_after_end(schedule_string, index):
    prior_schedule = schedule_string[:index]
    after_end = prior_schedule.count("END") > 0
    line_number = prior_schedule.count(os.linesep) + 1
    end_notification = LOG_AFTER_END_NOTIFICATION if after_end else ""

    return line_number, end_notification


def _log_date_injection(schedule_string, index, date):
    line_num, end_notification = _get_line_number_and_after_end(schedule_string, index)
    logger.info(
        "'{}' injected into schedule on line number {}{}".format(
            date, line_num, end_notification
        )
    )


def _log_template_injection(schedule_string, index, template, params, date):
    params = "({})".format(
        ", ".join(
            ["'{}' set to '{}'".format(key, value) for key, value in params.items()]
        )
    )
    _, end_notification = _get_line_number_and_after_end(schedule_string, index)
    logger.info(
        "'{}' with parameters {} injected into schedule on date {}{}".format(
            template, params, date, end_notification
        )
    )


def _get_dates_from_schedule(schedule_string):
    dates_in_schedule = re.findall("([0-9]{2} [A-Z]{3} [0-9]{4})", schedule_string)
    return [datetime.strptime(x, "%d %b %Y") for x in dates_in_schedule]


def _insert_in_schedule_string(schedule_string, insert_string, index):
    return schedule_string[:index] + insert_string + schedule_string[index:]


def _find_date_index(schedule_string, date):
    if date is None:
        index = len(schedule_string)
        return (index, 0)

    date_string = re.findall(
        FIND_DATE_REGEX.format(date.strftime("%d %b %Y").upper()), schedule_string
    )[0]
    index = schedule_string.index(date_string)

    return (index, len(date_string))


def _first_larger_than(val, val_list):
    idx = 0
    while val > val_list[idx]:
        idx += 1
    return val_list[idx]


def _inject_date(schedule_string, dates_in_schedule, date):
    new_date_string = INSERT_SCHEDULE_DATE.format(date.strftime("%d %b %Y")).upper()

    if dates_in_schedule[-1] < date:
        new_date_string = os.linesep + new_date_string
        insert_index = len(schedule_string)

    else:
        next_date = _first_larger_than(date, dates_in_schedule)
        insert_index, _ = _find_date_index(schedule_string, next_date)

    _log_date_injection(
        schedule_string, insert_index, date.strftime("%d %b %Y").upper()
    )
    return _insert_in_schedule_string(schedule_string, new_date_string, insert_index)


def _add_dates_to_schedule(schedule_string, dates):
    for date in dates:
        dates_in_schedule = _get_dates_from_schedule(schedule_string)
        dates_in_schedule.sort()
        schedule_string = _inject_date(schedule_string, dates_in_schedule, date)
    return schedule_string


def _add_dates_if_necessary(schedule_string, injections):
    dates_in_schedule = _get_dates_from_schedule(schedule_string)
    dates_in_injections = injections.keys()
    dates_not_in_schedule = set(dates_in_injections) - set(dates_in_schedule)

    if dates_not_in_schedule:
        schedule_string = _add_dates_to_schedule(
            schedule_string, sorted(list(dates_not_in_schedule))
        )

    return schedule_string


def _inject_templates(schedule_string, injections):
    def _format_rendered_string(string, template_file):
        start_line = "--start {t}{l}".format(t=template_file, l=os.linesep)
        end_line = "{l}{l}--end {t}{l}{l}{l}".format(t=template_file, l=os.linesep)
        formatted_string = start_line + string + end_line

        return formatted_string

    for date, jinja_dicts in injections.items():
        dates_in_schedule = _get_dates_from_schedule(schedule_string)

        try:
            next_date = dates_in_schedule[dates_in_schedule.index(date) + 1]
            string_to_inject = ""
        except IndexError:
            next_date = None
            string_to_inject = os.linesep

        insert_index, _ = _find_date_index(schedule_string, next_date)

        for jinja_dict in jinja_dicts:
            for template_file, params in jinja_dict.items():
                with open(template_file, "r") as f:
                    jinja_template = Template(f.read())
                rendered_string = jinja_template.render(**params)
                rendered_string = _format_rendered_string(
                    rendered_string, template_file
                )
                _log_template_injection(
                    schedule_string[:insert_index] + string_to_inject,
                    insert_index + len(string_to_inject),
                    template_file,
                    params,
                    date.strftime("%d %b %Y").upper(),
                )
                string_to_inject += rendered_string
        schedule_string = _insert_in_schedule_string(
            schedule_string, string_to_inject, insert_index
        )

    return schedule_string


def _get_transformed_injections(injection_json):
    injection_dict = defaultdict(list)

    for well_dict in injection_json:
        wellname = well_dict["name"]

        for op in well_dict["ops"]:
            op_copy = op.copy()
            date_string = op_copy.pop("date")
            date = datetime.strptime(date_string, "%d.%m.%Y")
            template = op_copy.pop("template")

            del op_copy["opname"]
            op_copy["name"] = wellname

            injection_dict[date].append({template: op_copy})

    ordered = OrderedDict(sorted(injection_dict.items()))
    return ordered


def _extract_comments(schedule_string):
    comment_placeholder_dict = {}
    regex_string = "{c}(.*?){l}".format(c=COMMENT_INDICATOR, l=os.linesep)
    comment_string = "{c}{{}}{l}".format(c=COMMENT_INDICATOR, l=os.linesep)
    comments_in_schedule = re.findall(regex_string, schedule_string)

    for index, comment in enumerate(comments_in_schedule):
        placeholder = PLACEHOLDER_INDICATOR.format(index)
        comment_placeholder_dict[index] = comment
        schedule_string = schedule_string.replace(
            comment_string.format(comment), comment_string.format(placeholder)
        )

    return schedule_string, comment_placeholder_dict


def _insert_extracted_comments(schedule_string, comment_placeholder_dict):
    for placeholder, comment in comment_placeholder_dict.items():
        schedule_string = schedule_string.replace(
            PLACEHOLDER_INDICATOR.format(placeholder), comment
        )

    return schedule_string


def merge_schedule(schedule_file, inject_file, output_file="merged_schedule.tmpl"):
    with open(schedule_file, "r") as f:
        schedule_string = f.read()

    with open(inject_file, "r") as f:
        injections = json.load(f)

    schedule_string, placeholder_dict = _extract_comments(schedule_string)
    injections = _get_transformed_injections(injections)
    schedule_string = _add_dates_if_necessary(schedule_string, injections)

    schedule_string = _inject_templates(schedule_string, injections)
    schedule_string = _insert_extracted_comments(schedule_string, placeholder_dict)

    with open(output_file, "w") as f:
        f.write(schedule_string)

    return schedule_string
