from pathlib import Path

from everest_models.jobs.fm_add_templates.cli import main_entry_point as add_templates
from everest_models.jobs.fm_schmerge.cli import main_entry_point as schmerge
from everest_models.jobs.fm_well_swapping.cli import main_entry_point as well_swapping


def test_well_swapping_workflow(copy_testdata_tmpdir) -> None:
    copy_testdata_tmpdir("workflows/well_swapping")

    well_swapping(
        [
            "run",
            "-p",
            "priorities.json",
            "-c",
            "constraints.json",
            "-o",
            "well_swap_output.json",
            "-w",
            "wells.json",
            "well_swap_config.yml",
        ]
    )
    add_templates(
        [
            "-c",
            "add_template_config.yml",
            "-i",
            "well_swap_output.json",
            "-o",
            "schmerge_input.json",
        ]
    )
    schmerge(
        [
            "-i",
            "schmerge_input.json",
            "-s",
            "raw_schedule.sch",
            "-o",
            "result_schedule.sch",
        ]
    )
    assert (
        Path("result_schedule.sch").read_bytes()
        == Path("expected_schedule.sch").read_bytes()
    )
