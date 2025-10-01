import io
import os
from contextlib import redirect_stdout
from os.path import relpath
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from ert.config import ErtConfig
from ert.ensemble_evaluator import EvaluatorServerConfig
from ert.plugins import ErtPluginContext
from ert.run_models.everest_run_model import EverestRunModel
from everest.bin.main import start_everest
from everest.config import EverestConfig
from everest.simulator.everest_to_ert import _everest_to_ert_config_dict
from ruamel.yaml import YAML

CONFIG_FILE = "everest/model/config.yml"


def dump_runmodel_agnostic(runmodel: EverestRunModel) -> str:
    runmodel.runpath_config.jobname_format_string = "EIGHTCELLS"
    runmodel.queue_config.queue_options.activate_script = ""
    job_script = runmodel.queue_config.queue_options.job_script
    job_script_dir = str(Path(job_script).parent)
    substitutions = (
        {
            e.executable: Path(e.executable).name
            for e in runmodel.forward_model_steps
            if Path(e.executable).is_absolute()
        }
        | {job_script_dir: "ert/bin"}
        | {os.getcwd(): "cwd"}
    )

    json_dump = runmodel.model_dump_json(indent=2)
    for old_value, new_value in substitutions.items():
        json_dump = json_dump.replace(old_value, new_value)

    return json_dump + "\n"


def test_conversion_of_eightcells_everestmodel_to_runmodel(
    copy_eightcells_test_data_to_tmp, snapshot
):
    config = EverestConfig.load_file(CONFIG_FILE)
    runmodel = EverestRunModel.create(config, "exp", "batch")
    snapshot.assert_match(dump_runmodel_agnostic(runmodel), "eightcells_runmodel.json")


def test_conversion_of_eightcells_everestmodel_to_runmodel_with_extra_summary_keys(
    copy_eightcells_test_data_to_tmp, snapshot
):
    extra_sum_keys = [
        "GOIR:PRODUC",
        "GOIT:INJECT",
        "GOIT:PRODUC",
        "GWPR:INJECT",
        "GWPR:PRODUC",
        "GWPT:INJECT",
        "GWPT:PRODUC",
        "GWIR:INJECT",
    ]

    config = EverestConfig.load_file(CONFIG_FILE)
    # The Everest config file will fail to load as an Eclipse data file
    config.export.keywords = extra_sum_keys

    runmodel = EverestRunModel.create(config, "exp", "batch")
    snapshot.assert_match(
        dump_runmodel_agnostic(runmodel), "eightcells_runmodel_with_extra_sum_keys.json"
    )


def test_init_eightcells_model(copy_eightcells_test_data_to_tmp):
    config = EverestConfig.load_file(CONFIG_FILE)
    ert_config = _everest_to_ert_config_dict(config)

    with ErtPluginContext() as ctx:
        ErtConfig.with_plugins(ctx).from_dict(config_dict=ert_config)


@pytest.mark.requires_eclipse
@pytest.mark.timeout(0)
@pytest.mark.xfail(
    reason="output is stochastic and we do not allow the algorithm to converge"
)
def test_eightcells_snapshot(snapshot, copy_eightcells_test_data_to_tmp):
    config = EverestConfig.load_file(CONFIG_FILE)

    run_model = EverestRunModel.create(config)
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


def test_lint_everest_models_jobs():
    config_file = relpath("tests/testdata/eightcells/everest/model/config.yml")
    config = EverestConfig.load_file(config_file).to_dict()
    # Check initial config file is valid
    assert len(EverestConfig.lint_config_dict(config)) == 0


def test_init_no_project_res(copy_eightcells_test_data_to_tmp):
    config_file = os.path.join("everest", "model", "config.yml")
    config = EverestConfig.load_file(config_file)
    EverestRunModel.create(config)


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
