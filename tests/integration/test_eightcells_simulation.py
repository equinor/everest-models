import io
import os
from contextlib import redirect_stdout
from os.path import relpath
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from ruamel.yaml import YAML

try:
    from ert.ensemble_evaluator import EvaluatorServerConfig
    from ert.plugins import ErtPluginContext
    from ert.run_models.everest_run_model import EverestRunModel
    from everest.bin.main import start_everest
    from everest.config import EverestConfig
except ImportError:
    pytest.skip("Skipping tests: 'ert' is not installed", allow_module_level=True)

CONFIG_FILE = "everest/model/config.yml"


@pytest.mark.usefixtures("use_site_configurations_with_no_queue_options")
@pytest.mark.timeout(0)
@pytest.mark.xfail(
    reason="output is stochastic and we do not allow the algorithm to converge"
)
def test_eightcells_snapshot(snapshot, copy_eightcells_test_data_to_tmp):
    config = EverestConfig.load_file(CONFIG_FILE)

    with ErtPluginContext() as runtime_plugins:
        run_model = EverestRunModel.create(config, runtime_plugins=runtime_plugins)
    evaluator_server_config = EvaluatorServerConfig()
    run_model.run_experiment(evaluator_server_config)

    best_batch = [b for b in run_model._ever_storage.data.batches if b.is_improvement][
        -1
    ]

    best_controls = best_batch.realization_controls
    best_objectives_csv = best_batch.perturbation_objectives
    best_objective_gradients_csv = best_batch.batch_objective_gradient

    def _is_close(data, snapshot_name):
        data = data.to_pandas()
        snapshot_data = pd.read_csv(snapshot.snapshot_dir / snapshot_name)
        if data.shape != snapshot_data.shape or not all(
            data.columns == snapshot_data.columns
        ):
            raise ValueError(
                f"Dataframes have different structures for {snapshot_name}"
                f"{data}\n\n{snapshot_data}"
            )
        tolerance = 1

        comparison = data.select_dtypes(include=[float, int]).apply(
            lambda col: np.isclose(col, snapshot_data[col.name], atol=tolerance)
        )

        # Check if all values match within the tolerance
        assert comparison.all().all(), (
            f"Values do not match for {snapshot_name} \n{data}\n\n{snapshot_data}"
        )

    _is_close(best_controls, "best_controls")
    _is_close(best_objectives_csv, "best_objectives_csv")
    _is_close(best_objective_gradients_csv, "best_objective_gradients_csv")


@pytest.mark.ert
def test_lint_everest_models_jobs():
    config_file = relpath("tests/testdata/eightcells/everest/model/config.yml")
    config = EverestConfig.load_file(config_file).to_dict()
    # Check initial config file is valid
    assert len(EverestConfig.lint_config_dict(config)) == 0


@pytest.mark.ert
def test_init_no_project_res(copy_eightcells_test_data_to_tmp):
    config_file = os.path.join("everest", "model", "config.yml")
    config = EverestConfig.load_file(config_file)

    with ErtPluginContext() as runtime_plugins:
        EverestRunModel.create(config, runtime_plugins=runtime_plugins)


@pytest.mark.ert
def test_everest_main_configdump_entry(copy_eightcells_test_data_to_tmp):
    out = io.StringIO()
    with redirect_stdout(out):
        start_everest(["everest", "render", "everest/model/config.yml"])
    yaml = YAML(typ="safe", pure=True)
    render_dict = yaml.load(out.getvalue())

    # Test whether the config file is correctly rendered with jinja
    assert (
        Path(render_dict["install_data"][0]["source"])
        == Path(os.getcwd())
        / "everest/model/../../eclipse/include/"
        "realizations/realization-<GEO_ID>/eclipse"
    )
