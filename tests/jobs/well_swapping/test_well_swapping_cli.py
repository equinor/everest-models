import json
from pathlib import Path
from typing import Tuple

import pytest
from everest_models.jobs.fm_well_swapping.cli import main_entry_point
from everest_models.jobs.shared.io_utils import load_json
from sub_testdata import WELL_SWAPPING as TEST_DATA


@pytest.mark.parametrize(
    "command",
    (
        pytest.param(("run", "well_swap_config.yml"), id="command structure"),
        pytest.param(("--config", "well_swap_config.yml"), id="legacy structure"),
    ),
)
def test_well_swapping_main_entrypoint_run(
    copy_testdata_tmpdir, command: Tuple[str]
) -> None:
    copy_testdata_tmpdir(TEST_DATA)
    output = "well_swap_output.json"
    main_entry_point(
        (
            *command,
            "--priorities",
            "priorities.json",
            "--constraints",
            "constraints.json",
            "--output",
            output,
            "--cases",
            "wells.json",
        )
    )
    assert Path("expected_output.json").read_bytes() == Path(output).read_bytes()


def test_well_swapping_main_entrypoint_parse(copy_testdata_tmpdir) -> None:
    copy_testdata_tmpdir(TEST_DATA)
    files = tuple(Path().glob("*.*"))
    with pytest.raises(SystemExit, match="0"):
        main_entry_point(("lint", "--cases", "wells.json", "well_swap_config.yml"))
    assert files == tuple(Path().glob("*.*"))


def test_well_swapping_main_entrypoint_parse_fault(
    copy_testdata_tmpdir, capsys: pytest.CaptureFixture
) -> None:
    copy_testdata_tmpdir(TEST_DATA)
    priorities = load_json("priorities.json")
    del priorities["WELL-1"]["1"]
    with open("priorities.json", mode="w") as fp:
        json.dump(priorities, fp)

    files = tuple(Path().glob("*.*"))
    with pytest.raises(SystemExit, match="2"):
        main_entry_point(("lint", "-p", "priorities.json", "well_swap_config.yml"))

    assert files == tuple(Path().glob("*.*"))
    _, err = capsys.readouterr()
    assert (
        "lint: error: argument -p/--priorities: All entries must contain the same amount of elements/indexes"
        in err
    )
