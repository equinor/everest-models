import logging
import pathlib
from typing import Any, Dict, Tuple

from pydantic import ConfigDict, Field, FilePath, NewPath, model_validator
from typing_extensions import Annotated

from everest_models.jobs.shared.currency import CURRENCY_CODES
from everest_models.jobs.shared.models import ModelConfig
from everest_models.jobs.shared.models.economics import CurrencyRate, EconomicConfig


logger = logging.getLogger(__name__)


def get(obj, key, default=None):
    if isinstance(obj, Dict):
        return obj.get(key, default)
    else:
        return getattr(obj, key, default)


def set(obj, key, value):
    if isinstance(obj, Dict):
        obj[key] = value
    else:
        setattr(obj, key, value)
    return obj


def has_and_not_empty(obj, key):
    if isinstance(obj, Dict):
        return key in obj and bool(obj[key])
    else:
        return hasattr(obj, key) and bool(getattr(obj, key))
    


class EclipseSummaryConfig(ModelConfig):
    model_config = ConfigDict(frozen=False)
    main: Annotated[pathlib.Path, Field(description="", frozen=True)]
    reference: Annotated[FilePath, Field(default=None, description="")]
    keys: Annotated[Tuple[str, ...], Field(default_factory=tuple, description="")]


class OutputConfig(ModelConfig):
    model_config = ConfigDict(frozen=False)
    file: Annotated[NewPath, Field(description="")]
    currency: Annotated[str, Field(default=None, description="")]
    currency_rate: Annotated[
        Tuple[CurrencyRate, ...], Field(default=None, description="")
    ]


class OilEquivalentConversionConfig(ModelConfig):
    oil: Annotated[Dict[str, float], Field(description="")]
    remap: Annotated[Dict[str, Dict[str, float]], Field(default=None, description="")]


class EconomicIndicatorConfig(EconomicConfig):
    summary: Annotated[EclipseSummaryConfig, Field(description="")]
    wells_input: Annotated[FilePath, Field(default=None, description="")]
    output: Annotated[OutputConfig, Field(description="")]
    oil_equivalent: Annotated[
        OilEquivalentConversionConfig, Field(default=None, description="")
    ]
    
    

     
    @model_validator(mode="before")
    @classmethod
    def populate_summary_keys(cls, values: Dict[str, Any]):
        if "summary" not in values or values["summary"] is None:
            print("summary not specified, defaulting")
            values["summary"]={'main': 'defaulting'}
            set(values["summary"], "keys", tuple(values["prices"]))

        elif not has_and_not_empty(values["summary"], "keys"):
            print("values[summary]",values["summary"])
            set(values["summary"], "keys", tuple(values["prices"]))
        return values


    @model_validator(mode="before")
    @classmethod
    def currency_rate_exist(cls, values):
        print("Input information:", values)

        # Handle output: create default if missing
        output = values.get("output")
        if output is None:
            output = {"file": "npvs"}
            values["output"] = output
            print("Created default output section:", output)
        elif isinstance(output, dict):
            if "file" not in output or output["file"] is None:
                output["file"] = "npvs"
                print("Set default file in dict output")
        else:
            # Output is already a model (OutputConfig) – reassign if needed
            if not hasattr(output, "file") or output.file is None:
                setattr(output, "file", "npvs")
                print("Set default file in model output")

        # Determine currency depending on type
        currency = (
            output.get("currency") if isinstance(output, dict)
            else getattr(output, "currency", None)
        )
        print("Detected currency:", currency)

        if currency is None:
            return values

        # Check currency_rate exists
        currency_rate = (
            output.get("currency_rate") if isinstance(output, dict)
            else getattr(output, "currency_rate", None)
        )
        if currency_rate:
            return values

        # Get exchange_rates
        exchange_rates = values.get("exchange_rates")
        print("Exchange rates:", exchange_rates)

        if not exchange_rates or currency not in exchange_rates:
            rate_value = [{"date": None, "value": 1.0}]
            print("Defaulting to rate 1.0")
        else:
            rate_value = tuple(
                {"date": rate["date"], "value": 1.0 / rate["value"]}
                if isinstance(rate, dict)
                else {"date": rate.date, "value": 1.0 / rate.value}
                for rate in exchange_rates[currency]
            )
            print("Computed inverted rates:", rate_value)

        # Set currency_rate
        if isinstance(output, dict):
            output["currency_rate"] = rate_value
        else:
            setattr(output, "currency_rate", rate_value)

        values["output"] = output
        print("Final output:", output)
        return values
