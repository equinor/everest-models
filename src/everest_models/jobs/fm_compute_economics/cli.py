import argparse
import logging

from everest_models.jobs.fm_compute_economics.manager import create_indicator
from everest_models.jobs.fm_compute_economics.parser import build_argument_parser
from everest_models.jobs.shared.models import Wells
from everest_models.jobs.shared.validators import parse_file

logger = logging.getLogger(__name__)


FULL_JOB_NAME = "Compute economics"


def _set_output_currency(currency, exchange_rates):
    if exchange_rates.get(currency, None) is None:
        rate_default_currency = None
    else:
        rate_default_currency = tuple(
            {"date": rate.date, "value": 1.0 / rate.value}
            for rate in exchange_rates[currency]
        )
    return rate_default_currency


def _overwrite_economic_indicator_config(
    options: argparse.Namespace, field: str, index: int = 1
):
    if (value := getattr(options, field, None)) is not None:
        if "date" in field:
            instance = options.config.dates
            setattr(
                instance, field, value[index] if isinstance(value, tuple) else value
            )
        elif field == "input":
            instance = options.config.wells_input = (
                value[index] if isinstance(value, tuple) else value
            )
        elif field == "summary_reference":
            instance = options.config.summary.reference = (
                value[index] if isinstance(value, tuple) else value
            )
        elif field == "output":
            options.config.output.file = (
                value[index] if isinstance(value, tuple) else value
            )
        elif field == "output_currency":
            options.config.output.currency = (
                value[index] if isinstance(value, tuple) else value
            )
            currency_value = _set_output_currency(
                options.config.output.currency, options.config.exchange_rates
            )
            options.config.output.currency_rate = currency_value
        else:
            instance = options.config
            setattr(
                instance, field, value[index] if isinstance(value, tuple) else value
            )
        logger.info(f"Overwrite config field with '{field}' CLI argument: {value}")


def main_entry_point(args=None):
    args_parser = build_argument_parser()
    options = args_parser.parse_args(args=args)

    if options.lint:
        args_parser.exit()

    for field in (
        "summary_reference",
        "multiplier",
        "input",
        "default_exchange_rate",
        "default_discount_rate",
        "start_date",
        "end_date",
        "ref_date",
        "output",
        "output_currency",
    ):
        _overwrite_economic_indicator_config(options, field)

    logger.info(f"Initializing economic_indicator calculation with options {options}")

    if bool(options.config.well_costs) ^ bool(options.config.wells_input):
        args_parser.error(
            "-c/--config argument file keys 'well_costs' and 'wells_input' "
            "must always be paired; one of the two is missing."
        )

    economic_indicator = create_indicator(
        options.calculation, config=options.config
    ).compute(
        {
            well.name: well.completion_date or well.readydate
            for well in (
                parse_file(options.config.wells_input, Wells)
                if options.config.wells_input
                else {}
            )
        }
    )

    options.config.output.file.write_text(f"{economic_indicator:.2f}")
