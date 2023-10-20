import datetime
import pathlib

import pytest
from sub_testdata import SCHMERGE as TEST_DATA

from everest_models.jobs.fm_schmerge.tasks import merge_operations_onto_schedule
from everest_models.jobs.shared.models.phase import PhaseEnum

SCHEDULE_HEAD = """
RPTRST
   BASIC=3 FREQ=3 /"""


@pytest.mark.parametrize(
    "operations, expected",
    (
        pytest.param(
            {datetime.date(2005, 1, 1): []},
            "\n\n-- MODIFIED by schmerge forward model\n\n"
            "DATES\n 01 JAN 2000 /\n/\n\nDATES\n 01 JAN 2001 /\n/\n\n"
            "DATES\n 01 JAN 2005 / --ADDED\n/\n\n",
            id="add_single_date",
        ),
        pytest.param(
            {datetime.date(2000, 3, 1): [], datetime.date(2005, 1, 1): []},
            "\n\n-- MODIFIED by schmerge forward model\n\n"
            "DATES\n 01 JAN 2000 /\n/\n\nDATES\n 01 MAR 2000 / --ADDED\n/\n\n"
            "DATES\n 01 JAN 2001 /\n/\n\nDATES\n 01 JAN 2005 / --ADDED\n/\n\n",
            id="add_multi_dates",
        ),
        pytest.param(
            {datetime.date(2000, 1, 1): []},
            "\n\n-- MODIFIED by schmerge forward model\n\n"
            "DATES\n 01 JAN 2000 /\n/\n\nDATES\n 01 JAN 2001 /\n/\n",
            id="existing_date",
        ),
        pytest.param(
            {
                datetime.date(2000, 1, 1): [
                    {
                        "template": pathlib.Path("wconinje.jinja"),
                        "template_map": {
                            "name": "SINGLE",
                            "phase": PhaseEnum.WATER,
                            "rate": 300.4,
                        },
                    }
                ]
            },
            "\n\n-- MODIFIED by schmerge forward model\n\n"
            "DATES\n 01 JAN 2000 /\n/\n\n--start wconinje.jinja\n\nWCONINJE\n  "
            "'SINGLE'  'WATER'  'OPEN'  'RATE' 300.4   1* 320  1*  1*    1*   /"
            "\n/\n\n--end wconinje.jinja\n\nDATES\n 01 JAN 2001 /\n/\n",
            id="single_operation_existing_date",
        ),
        pytest.param(
            {
                datetime.date(2000, 3, 1): [
                    {
                        "template": pathlib.Path("wconinje.jinja"),
                        "template_map": {
                            "name": "SINGLE",
                            "phase": PhaseEnum.WATER,
                            "rate": 300.4,
                        },
                    }
                ]
            },
            "\n\n-- MODIFIED by schmerge forward model\n\n"
            "DATES\n 01 JAN 2000 /\n/\n\nDATES\n 01 MAR 2000 / --ADDED\n/\n\n"
            "--start wconinje.jinja\n\nWCONINJE\n  "
            "'SINGLE'  'WATER'  'OPEN'  'RATE' 300.4   1* 320  1*  1*    1*   /"
            "\n/\n\n--end wconinje.jinja\n\nDATES\n 01 JAN 2001 /\n/\n",
            id="single_operation_new_date",
        ),
        pytest.param(
            {
                datetime.date(2000, 3, 1): [
                    {
                        "template": pathlib.Path("wconinje.jinja"),
                        "template_map": {
                            "name": "MULTI1",
                            "phase": PhaseEnum.WATER,
                            "rate": 300.4,
                        },
                    },
                    {
                        "template": pathlib.Path("welopen.jinja"),
                        "template_map": {
                            "name": "MULTI2",
                        },
                    },
                ]
            },
            "\n\n-- MODIFIED by schmerge forward model\n\n"
            "DATES\n 01 JAN 2000 /\n/\n\nDATES\n 01 MAR 2000 / --ADDED\n/\n\n"
            "--start wconinje.jinja\n\nWCONINJE\n  'MULTI1'  'WATER'  "
            "'OPEN'  'RATE' 300.4   1* 320  1*  1*    1*   /\n/\n\n"
            "--end wconinje.jinja\n\n--start welopen.jinja\n\nWELOPEN\n  "
            "'MULTI2' 'OPEN' /\n/\n\n--end welopen.jinja\n\nDATES\n 01 JAN 2001 /\n/\n",
            id="multi_operation_single_date",
        ),
    ),
)
def test_insert_operations(copy_testdata_tmpdir, operations, expected):
    copy_testdata_tmpdir(f"{TEST_DATA}/files")
    assert (
        merge_operations_onto_schedule(
            operations,
            f"{SCHEDULE_HEAD}\n\nDATES\n 01 JAN 2000 /\n/\n\nDATES\n 01 JAN 2001 /\n/\n",
        )
        == SCHEDULE_HEAD + expected
    )


def test_insert_operations_no_initial_date():
    assert merge_operations_onto_schedule(
        {datetime.date(2000, 3, 1): [], datetime.date(2005, 1, 1): []},
        f"{SCHEDULE_HEAD}\n",
    ) == (
        f"{SCHEDULE_HEAD}\n\n-- MODIFIED by schmerge forward model\n\n"
        "DATES\n 01 MAR 2000 / --ADDED\n/\n\n"
        "DATES\n 01 JAN 2005 / --ADDED\n/\n\n"
    )
