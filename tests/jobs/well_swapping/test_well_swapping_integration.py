from pathlib import Path
from typing import Callable

import pytest
from ert.ensemble_evaluator.config import EvaluatorServerConfig
from ert.run_models.everest_run_model import EverestRunModel
from everest.config import EverestConfig


@pytest.mark.usefixtures("use_site_configurations_with_no_queue_options")
@pytest.mark.integration_test
@pytest.mark.parametrize("config", ("array", "index"))
def test_state_modifier_workflow_run(
    config: str,
    copy_testdata_tmpdir: Callable[[str | None], Path],
) -> None:
    cwd = copy_testdata_tmpdir("open_shut_state_modifier")

    run_model = EverestRunModel.create(
        EverestConfig.load_file(f"everest/model/{config}.yml")
    )
    evaluator_server_config = EvaluatorServerConfig()
    run_model.run_experiment(evaluator_server_config)
    paths = list(Path.cwd().glob("**/evaluation_0/RESULT.SCH"))
    assert paths
    for path in paths:
        assert path.read_bytes() == (cwd / "eclipse/model/EXPECTED.SCH").read_bytes()
