import datetime
from copy import deepcopy
from typing import NamedTuple, Tuple

import pytest

from everest_models.jobs.fm_select_wells.tasks import get_well_number, select_wells
from everest_models.jobs.shared.models import Wells
from everest_models.jobs.shared.validators import parse_file


class FileOptions(NamedTuple):
    file_path: float = 0.05
    real_bounds: Tuple[int, int] = (0, 47)
    scaled_bounds: Tuple[float, float] = (0.0, 1.0)
    lint: bool = False


class ValueOptions(NamedTuple):
    well_number: float = 2.0
    lint: bool = False


@pytest.fixture(scope="module")
def well_list(path_test_data):
    return parse_file(path_test_data / "select_wells/input.json", Wells)


def test_get_well_number_no_well_number():
    class Options(NamedTuple):
        lint: bool = False

    assert get_well_number(Options(), None) is None  # type: ignore
    assert get_well_number(Options(lint=True), None) is None  # type: ignore


def test_get_well_number():
    value = get_well_number(ValueOptions(), None)  # type: ignore
    assert isinstance(value, int)
    assert value == 2


def test_get_well_number_lint():
    value = get_well_number(ValueOptions(lint=True), None)  # type: ignore
    assert isinstance(value, float)
    assert value == 2.0


def test_get_well_number_file_path():
    value = get_well_number(FileOptions(), None)  # type: ignore
    assert isinstance(value, int)
    assert value == 2


def test_get_well_number_file_path_lint():
    value = get_well_number(FileOptions(lint=True), None)  # type: ignore
    assert isinstance(value, float)
    assert value == 0.05


def test_get_well_number_file_path_bad_bounds():
    def write_error(value):
        assert "Invalid real_bounds: lower bound greater than upper, (3, 1)" in value
        assert (
            "Invalid scaled_bounds: lower bound greater than upper, (3.2, 0.14)"
            in value
        )

    get_well_number(
        FileOptions(real_bounds=(3, 1), scaled_bounds=(3.2, 0.14)),  # type: ignore
        write_error,
    )


def test_select_wells_no_change(well_list):
    wells = len(well_list.root)
    select_wells(well_list, None, None)
    assert wells == len(well_list.root)


@pytest.mark.parametrize(
    "date, length",
    (
        pytest.param(datetime.date(2022, 12, 31), 1, id="2022-12-31"),
        pytest.param(datetime.date(2023, 3, 22), 4, id="2023-03-22"),
    ),
)
def test_select_wells_dates(date: datetime.date, length: int, well_list):
    wells = deepcopy(well_list)
    n_wells = len(wells.root)
    select_wells(wells, date, None)
    selected_len = len(wells.root)
    assert n_wells != selected_len
    assert selected_len == length


def test_select_wells_dates_n_well_number(well_list):
    wells = deepcopy(well_list)
    select_wells(wells, datetime.date(2023, 3, 22), 2)
    assert [well.readydate for well in wells] == [
        datetime.date(2022, 12, 1),
        datetime.date(2023, 1, 21),
    ]
