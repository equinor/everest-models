from collections.abc import Callable, Iterator
from copy import deepcopy
from typing import Any

import pytest
from jobs.compute_economics.parser import (
    MockParser,
    Options,
    ecl_summary_economic_indicator,
)
from sub_testdata import ECONOMIC_INDICATOR as TEST_DATA

from everest_models.jobs.fm_compute_economics import cli
from everest_models.jobs.fm_compute_economics.economic_indicator_config_model import (
    EconomicIndicatorConfig,
)
from everest_models.jobs.fm_compute_economics.manager import EclipseSummary
from everest_models.jobs.shared.validators import valid_input_file


@pytest.fixture(scope="package")
def economic_indicator_config(path_test_data) -> dict[str, Any]:
    return valid_input_file(path_test_data / TEST_DATA / "input_data.yml")


@pytest.fixture(scope="module")
def economic_indicator_summary():
    return ecl_summary_economic_indicator()


@pytest.fixture
def get_summary_patch(monkeypatch):
    class MockGet:
        def __init__(self) -> None:
            self.respondses = iter([ecl_summary_economic_indicator(), None])

        def __call__(self, _):
            return next(self.respondses)

    monkeypatch.setattr(EclipseSummary, "get_summary", MockGet())


@pytest.fixture
def modify_economic_config(
    economic_indicator_config,
) -> Iterator[Callable[[str | None, str | None, bool], dict[str, Any]]]:
    def build_config(
        wells_input: str | None = None,
        currency: str | None = None,
        remove_well_costs: bool = False,
    ) -> dict[str, Any]:
        config = deepcopy(economic_indicator_config)
        if wells_input:
            config["wells_input"] = wells_input
        if currency:
            config["output"]["currency"] = currency
        if remove_well_costs:
            del config["well_costs"]
        return config

    yield build_config


@pytest.fixture
def build_economic_parser_patch(
    monkeypatch,
) -> Iterator[Callable[[dict[str, Any]], None]]:
    def patch(config: dict[str, Any], **kwargs) -> None:
        monkeypatch.setattr(
            cli,
            "build_argument_parser",
            lambda: MockParser(
                options=Options(
                    config=EconomicIndicatorConfig.model_validate(config),
                    **kwargs,
                )
            ),
        )

    yield patch
