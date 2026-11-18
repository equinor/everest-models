import datetime
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ruamel.yaml import YAML

from everest_models.jobs.shared.arguments import (
    add_lint_argument,
    get_parser,
)
from everest_models.jobs.shared.validators import (
    is_writable_path,
    valid_ecl_summary,
    valid_iso_date,
)

_AGGREGATIONS = {"min", "max", "mean", "median"}


@dataclass
class RegionConfig:
    region_number: int
    output: str
    key: str
    aggregation: str | None = None
    output_date: str | None = None
    unit_conversion: float = 1.0
    start_date: datetime.date | None = None
    end_date: datetime.date | None = None


@dataclass
class SectionConfig:
    fip_key: str
    fip_region: list[RegionConfig]


@dataclass
class KeywordConfig:
    key: str
    output: str
    aggregation: str | None = None
    output_date: str | None = None
    unit_conversion: float = 1.0
    start_date: datetime.date | None = None
    end_date: datetime.date | None = None


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def _resolve_unit_conversion(entry: dict[str, Any], context: str) -> float:
    try:
        value = _resolve_alias(entry, "unit-conversion", "u", context)
        conversion = float(1.0 if value is None else value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{context}: unit-conversion must be numeric") from error
    if conversion == 0:
        raise ValueError(f"{context}: unit-conversion must be non-zero")
    return conversion


def _resolve_output(entry: dict[str, Any], context: str) -> str:
    if "output" in entry and "o" in entry:
        raise ValueError(f"{context}: use either 'output' or 'o', not both")
    output = entry.get("output", entry.get("o"))
    if output is None:
        raise ValueError(f"{context}: missing required key 'output' or 'o'")
    return str(output).strip()


def _resolve_alias(
    entry: dict[str, Any], long_name: str, short_name: str, context: str
) -> Any:
    if long_name in entry and short_name in entry:
        raise ValueError(
            f"{context}: use either '{long_name}' or '{short_name}', not both"
        )
    return entry.get(long_name, entry.get(short_name))


def _resolve_selection(
    entry: dict[str, Any], context: str
) -> tuple[str | None, str | None]:
    new_keys = {"aggregation", "output-date"} & entry.keys()
    if len(new_keys) > 1:
        raise ValueError(
            f"{context}: use either 'aggregation' or 'output-date', not both"
        )

    if "aggregation" in entry:
        value = entry["aggregation"]
        aggregation = str(value).strip().lower() if value is not None else ""
        if not aggregation:
            return None, None
        if aggregation not in _AGGREGATIONS:
            raise ValueError(
                f"{context}: aggregation must be min, max, mean, or median"
            )
        return aggregation, None

    if "output-date" in entry:
        value = entry["output-date"]
        return None, str(value).strip() or None if value is not None else None

    return None, None


def _resolve_date(
    entry: dict[str, Any], key: str, context: str
) -> datetime.date | None:
    value = _resolve_alias(
        entry, key, {"start-date": "sd", "end-date": "ed"}[key], context
    )
    if value is None:
        return None
    try:
        return datetime.date.fromisoformat(str(value))
    except ValueError as error:
        raise ValueError(f"{context}: {key} must be an ISO date") from error


def _validate_keys(entry: dict[str, Any], allowed: set[str], context: str) -> None:
    unexpected = sorted(set(entry) - allowed)
    if unexpected:
        raise ValueError(f"{context}: unsupported key(s): {', '.join(unexpected)}")


def _parse_region(raw_region: Any, index: int, section_name: str) -> RegionConfig:
    if not isinstance(raw_region, dict):
        raise ValueError(f"Section '{section_name}', region #{index}: expected mapping")
    context = f"Section '{section_name}', region #{index}"
    _validate_keys(
        raw_region,
        {
            "region-number",
            "output",
            "o",
            "aggregation",
            "output-date",
            "key",
            "k",
            "unit-conversion",
            "u",
            "start-date",
            "sd",
            "end-date",
            "ed",
        },
        context,
    )
    key = _resolve_alias(raw_region, "key", "k", context)
    if key is None:
        raise ValueError(f"{context}: missing required key 'key' or 'k'")
    aggregation, output_date = _resolve_selection(raw_region, context)
    return RegionConfig(
        region_number=int(raw_region["region-number"]),
        output=_resolve_output(raw_region, context),
        aggregation=aggregation,
        output_date=output_date,
        key=str(key).strip(),
        unit_conversion=_resolve_unit_conversion(raw_region, context),
        start_date=_resolve_date(raw_region, "start-date", context),
        end_date=_resolve_date(raw_region, "end-date", context),
    )


def _parse_section(raw_section: Any, index: int) -> SectionConfig:
    if not isinstance(raw_section, dict):
        raise ValueError(f"Section #{index}: expected mapping")
    context = f"Section #{index}"
    _validate_keys(raw_section, {"fip-key", "fip-region"}, context)
    for key in ("fip-key", "fip-region"):
        if key not in raw_section:
            raise ValueError(f"{context}: missing required key '{key}'")
    keyword = str(raw_section["fip-key"]).strip().upper()
    regions = [
        _parse_region(region, region_index, keyword)
        for region_index, region in enumerate(
            _as_list(raw_section["fip-region"]), start=1
        )
    ]
    return SectionConfig(keyword, regions)


def _parse_keyword_entry(raw_entry: Any, index: int) -> KeywordConfig:
    if not isinstance(raw_entry, dict):
        raise ValueError(f"Keyword section #{index}: expected mapping")
    context = f"Keyword section #{index}"
    _validate_keys(
        raw_entry,
        {
            "key",
            "k",
            "output",
            "o",
            "unit-conversion",
            "u",
            "start-date",
            "sd",
            "end-date",
            "ed",
            "aggregation",
            "output-date",
        },
        context,
    )
    key = _resolve_alias(raw_entry, "key", "k", context)
    if key is None:
        raise ValueError(f"{context}: missing required key 'key' or 'k'")
    _resolve_output(raw_entry, context)
    aggregation, output_date = _resolve_selection(raw_entry, context)
    return KeywordConfig(
        key=str(key).strip(),
        output=_resolve_output(raw_entry, context),
        aggregation=aggregation,
        output_date=output_date,
        unit_conversion=_resolve_unit_conversion(raw_entry, context),
        start_date=_resolve_date(raw_entry, "start-date", context),
        end_date=_resolve_date(raw_entry, "end-date", context),
    )


def load_static_config(config_path: Path) -> dict[str, Any]:
    yaml = YAML(typ="safe")
    yaml.allow_duplicate_keys = False
    with config_path.open(encoding="utf-8") as config_file:
        config = yaml.load(config_file) or {}
    if not isinstance(config, dict):
        raise ValueError("Top-level YAML must be a mapping")
    return config


def build_argument_parser(skip_type=False):
    description = (
        "Module to extract Summary keyword data for single date or date interval"
    )
    parser, requird_group = get_parser(description=description)

    requird_group.add_argument(
        "-s",
        "--summary",
        type=valid_ecl_summary if not skip_type else str,
        help="Link to summary file",
    )
    requird_group.add_argument(
        "-o",
        "--output",
        type=is_writable_path if not skip_type else str,
        help="Name of output file",
    )
    parser.add_argument(
        "-c",
        "--config",
        type=Path if not skip_type else str,
        help="Link to YAML configuration",
    )
    add_lint_argument(parser)
    parser.add_argument(
        "-sd",
        "--start-date",
        type=valid_iso_date,
        help="Start date for an interval; if omitted, extract a single value "
        "at the end date or the last report date",
    )
    requird_group.add_argument(
        "-ed",
        "--end-date",
        "--date",
        type=valid_iso_date,
        help="End date for the summary key interval or date for which to "
        "extract a summary key value; defaults to the last report date",
    )
    requird_group.add_argument("-k", "--key", type=str, help="Summary key")
    parser.add_argument(
        "--aggregation",
        choices=sorted(_AGGREGATIONS),
        default=None,
        help="Statistic over the selected date range; defaults to the full time series",
    )
    parser.add_argument(
        "--output-date",
        type=valid_iso_date,
        default=None,
        help="Select one exact summary report date",
    )
    parser.add_argument(
        "--diff",
        action="store_true",
        help="Calculate the difference between the end date and start date",
    )
    parser.add_argument(
        "-u",
        "--unit-conversion",
        type=float,
        default=1.0,
        help="Divide the extracted value by a unit conversion factor",
    )
    return parser


args_parser = build_argument_parser()
