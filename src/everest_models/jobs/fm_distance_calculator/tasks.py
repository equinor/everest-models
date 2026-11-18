from __future__ import annotations

import math
import statistics
from collections.abc import Callable, Iterable, Sequence
from datetime import date
from functools import cache, partial
from pathlib import Path
from typing import Any

from everest_models.jobs.shared.resinsight import rips

from .config_model import DistanceCalculation, DistanceConfig, Point, PropertyFilter

_GRID_INDEX = 0

type _Dimensions = tuple[int, int, int]
type _IndexedDistances = Iterable[tuple[int, float]]
type _DistanceLookup = tuple[
    Callable[[set[int]], _IndexedDistances], Callable[[], Sequence[float]]
]
type _TargetLookup = Callable[[DistanceCalculation], _DistanceLookup]
type _CellSelector = Callable[[PropertyFilter | None], set[int]]


def point_to_segment_distance_3d(
    point: tuple[float, float, float],
    start: tuple[float, float, float],
    end: tuple[float, float, float],
) -> float:
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    dz = end[2] - start[2]
    length_squared = dx * dx + dy * dy + dz * dz
    if length_squared == 0.0:
        return math.dist(point, start)
    fraction = (
        (point[0] - start[0]) * dx
        + (point[1] - start[1]) * dy
        + (point[2] - start[2]) * dz
    ) / length_squared
    fraction = max(0.0, min(1.0, fraction))
    nearest = (
        start[0] + fraction * dx,
        start[1] + fraction * dy,
        start[2] + fraction * dz,
    )
    return math.dist(point, nearest)


def aggregate_distance(
    selected_distances: _IndexedDistances,
    aggregation: str,
) -> tuple[int | None, float | None]:
    if aggregation not in {"min", "max", "mean", "median"}:
        raise ValueError(
            f"Unsupported aggregation {aggregation!r}; expected min, max, mean, or median."
        )
    candidates = [
        (index, distance)
        for index, distance in selected_distances
        if math.isfinite(distance) and distance > 0.0
    ]
    if not candidates:
        return None, None
    if aggregation == "min":
        return min(candidates, key=lambda candidate: candidate[1])
    if aggregation == "max":
        return max(candidates, key=lambda candidate: candidate[1])
    values = [distance for _, distance in candidates]
    if aggregation == "mean":
        return None, statistics.fmean(values)
    return None, statistics.median(values)


def write_property(
    paths: Sequence[Path], keyword: str, values: Sequence[float]
) -> None:
    for path in paths:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as handle:
            handle.write(f"{keyword}\n")
            for start in range(0, len(values), 5):
                row = values[start : start + 5]
                handle.write(
                    "".join(
                        f"{(value if math.isfinite(value) else 0.0):17.9g}"
                        for value in row
                    )
                    + "\n"
                )
            handle.write("/\n")


def write_scalar(paths: Sequence[Path], value: float) -> None:
    if not math.isfinite(value):
        raise ValueError(f"Cannot write non-finite scalar value: {value!r}")
    for path in paths:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"{value:.9g}\n", encoding="utf-8")


def _find_faults(case: Any, fault_names: set[str]) -> tuple[Any, dict[str, list[Any]]]:
    if not fault_names:
        return None, {}

    views = case.views()
    if not views:
        created_view = case.create_view()
        views = [created_view] if created_view is not None else []
    observed_faults: set[str] = set()
    for candidate_view in views:
        if not hasattr(candidate_view, "fault_collection"):
            continue
        fault_collection = candidate_view.fault_collection()
        faults = fault_collection.faults() if fault_collection else []
        observed_faults.update(fault.fault_name for fault in faults)
        selected = {
            name: [fault for fault in faults if fault.fault_name == name]
            for name in fault_names
        }
        if all(selected.values()):
            return candidate_view, selected
    raise RuntimeError(
        f"Faults {sorted(fault_names)} were not found in the loaded case. "
        f"Available faults: {sorted(observed_faults)}"
    )


def _indexed_distances(
    distances: Sequence[float], indices: set[int]
) -> _IndexedDistances:
    return ((index, distances[index]) for index in indices)


def _cache_cell_distances(
    centers: Sequence[Point], measure: Callable[[Point], float]
) -> _DistanceLookup:
    selected: dict[int, float] = {}
    full_grid: list[float] | None = None

    def full_grid_distances() -> Sequence[float]:
        nonlocal full_grid
        if full_grid is None:
            full_grid = [
                selected[index] if index in selected else measure(center)
                for index, center in enumerate(centers)
            ]
            selected.clear()
        return full_grid

    def distances_for(indices: set[int]) -> _IndexedDistances:
        if full_grid is not None or len(indices) == len(centers):
            yield from _indexed_distances(full_grid_distances(), indices)
            return
        for index in indices:
            if index not in selected:
                selected[index] = measure(centers[index])
            yield index, selected[index]

    return distances_for, full_grid_distances


def _check_length[T](
    values: Sequence[T], expected: int, description: str
) -> Sequence[T]:
    if len(values) != expected:
        raise RuntimeError(f"Expected {expected} {description}, got {len(values)}.")
    return values


def _flat_index(ijk: Any, dimensions: _Dimensions) -> int:
    nx, ny, _ = dimensions
    return ijk.i + ijk.j * nx + ijk.k * nx * ny


def _one_based_ijk(index: int, dimensions: _Dimensions) -> tuple[int, int, int]:
    nx, ny, _ = dimensions
    return index % nx + 1, (index // nx) % ny + 1, index // (nx * ny) + 1


def _cell_centers(grid: Any, total_cells: int) -> list[Point]:
    centers = _check_length(grid.cell_centers(), total_cells, "cell centers")
    if not centers:
        raise RuntimeError("The grid contains no cell centers.")
    return [(center.x, center.y, center.z) for center in centers]


def _fault_distances(
    name: str, *, case: Any, view: Any, faults: dict[str, list[Any]], total_cells: int
) -> Sequence[float]:
    # resinsight will create a map of distances towards every cell from a fault
    # hence we don't require cell indices to based distance calculations on.
    result = view.add_fault_distance(f"PY_FAULTDIST_{name}", faults[name])
    return _check_length(
        case.grid_property(
            rips.PropertyType.GENERATED, result.result_name, 0, _GRID_INDEX
        ),
        total_cells,
        f"{name} fault distances",
    )


def _well_centers(
    name: str,
    *,
    case: Any,
    cell_centers: Callable[[], Sequence[Point]],
    dimensions: _Dimensions,
    report_count: int,
) -> list[Point]:
    wells = case.simulation_wells()
    well = next((well for well in wells if well.name == name), None)
    if well is None:
        raise RuntimeError(
            f"Simulation well {name!r} not found. Available: "
            f"{sorted(well.name for well in wells)}"
        )
    connected_indices = {
        _flat_index(connection.ijk, dimensions)
        for step in range(report_count)
        for connection in well.cells(step)
        if connection.grid_index == _GRID_INDEX
    }
    if not connected_indices:
        raise RuntimeError(
            f"Simulation well {name!r} has no connections in grid {_GRID_INDEX}."
        )
    centers = cell_centers()
    return [centers[index] for index in sorted(connected_indices)]


def _make_target_lookup(
    case: Any,
    fault_names: set[str],
    total_cells: int,
    cell_centers: Callable[[], Sequence[Point]],
    well_centers: Callable[[str], Sequence[Point]],
) -> _TargetLookup:
    find_faults = cache(partial(_find_faults, case, fault_names))

    @cache
    def fault_distances(name: str) -> Sequence[float]:
        view, faults = find_faults()
        return _fault_distances(
            name,
            case=case,
            view=view,
            faults=faults,
            total_cells=total_cells,
        )

    @cache
    def well_distances(name: str) -> _DistanceLookup:
        connections = well_centers(name)
        return _cache_cell_distances(
            cell_centers(),
            lambda center: min(math.dist(center, well) for well in connections),
        )

    @cache
    def polygon_depth_sign() -> float:
        return -1.0 if sum(z for _, _, z in cell_centers()) < 0.0 else 1.0

    @cache
    def polyline_distances(points: tuple[Point, ...]) -> _DistanceLookup:
        depth_sign = polygon_depth_sign()
        polyline = [
            (easting, northing, depth_sign * depth)
            for easting, northing, depth in points
        ]
        segments = list(zip(polyline, polyline[1:], strict=False))
        return _cache_cell_distances(
            cell_centers(),
            lambda center: min(
                point_to_segment_distance_3d(center, start, end)
                for start, end in segments
            ),
        )

    def target_for(calculation: DistanceCalculation) -> _DistanceLookup:
        if calculation.type == "fault":
            distances = fault_distances(calculation.name)
            return partial(_indexed_distances, distances), lambda: distances
        if calculation.type == "well":
            return well_distances(calculation.name)
        return polyline_distances(calculation.points)

    return target_for


def _time_step_indices(
    step_dates: Sequence[date], report_date: date | None
) -> Iterable[int]:
    if report_date is None:
        if not step_dates:
            raise RuntimeError(
                "No report dates are available for dynamic property filtering."
            )
        return range(len(step_dates))
    if report_date not in step_dates:
        available_dates = [step.isoformat() for step in step_dates]
        raise RuntimeError(
            f"Report date {report_date} not found. Available: {available_dates}"
        )
    return [step_dates.index(report_date)]


def _make_cell_selector(
    case: Any, active_indices: set[int], step_dates: Sequence[date], total_cells: int
) -> _CellSelector:
    @cache
    def matching_indices(
        keyword: str, threshold: float, report_date: date | None
    ) -> set[int]:
        matches: set[int] = set()
        for step in _time_step_indices(step_dates, report_date):
            values = _check_length(
                case.grid_property(
                    rips.PropertyType.DYNAMIC_NATIVE, keyword, step, _GRID_INDEX
                ),
                total_cells,
                f"{keyword} values",
            )
            matches.update(
                index
                for index in active_indices
                if math.isfinite(values[index]) and values[index] >= threshold
            )
        return matches

    def selected_cells(property_filter: PropertyFilter | None) -> set[int]:
        if property_filter is None:
            return active_indices
        return matching_indices(
            property_filter.name.upper(),
            property_filter.threshold,
            property_filter.date,
        )

    return selected_cells


def _filter_label(property_filter: PropertyFilter | None) -> str:
    if property_filter is None:
        return "all active cells (no 'property' set)"
    return (
        f"{property_filter.name.upper()} >= {property_filter.threshold:g} "
        f"@ {property_filter.date or 'all timesteps'}"
    )


def _run_calculation(
    calculation: DistanceCalculation,
    target_for: _TargetLookup,
    indices: set[int],
    scalar_path: Path,
    map_path: Path | None,
) -> tuple[float, int | None]:
    multiplier = calculation.multiplier
    if not indices:
        raise _no_distance(calculation)
    distances_for, full_grid_distances = target_for(calculation)
    index, distance = aggregate_distance(
        distances_for(indices), calculation.aggregation
    )
    if distance is None:
        raise _no_distance(calculation)

    if map_path is not None:
        write_property(
            [map_path],
            calculation.output,
            [distance * multiplier for distance in full_grid_distances()],
        )
    converted_distance = distance * multiplier
    write_scalar([scalar_path], converted_distance)
    return converted_distance, index


def _report_calculation(
    calculation: DistanceCalculation,
    cell_count: int,
    distance_result: tuple[float, int | None],
    dimensions: _Dimensions,
    scalar_path: Path,
    map_path: Path | None,
    *,
    well_connection_count: int | None,
) -> None:
    distance, index = distance_result
    multiplier = calculation.multiplier
    if calculation.type == "polygon":
        target_label = f"polyline of {len(calculation.points)} points"
    else:
        target_label = f"{calculation.type} {calculation.name}"
    filter_label = _filter_label(calculation.property)
    print(f"\n{calculation.output}  ->  {target_label}")
    print(f"  filter: {filter_label} ({cell_count} cells)")
    if calculation.type == "well" and well_connection_count is not None:
        print(f"  Unique {calculation.name} connection cells: {well_connection_count}")
    result = f"  {calculation.aggregation} distance: {distance:.2f}"
    if multiplier != 1:
        result += f" (multiplied by {multiplier:g})"
    if index is not None:
        result += f" at ijk {_one_based_ijk(index, dimensions)}"
    print(result)
    print(f"  wrote scalar: {scalar_path}")
    if map_path is not None:
        print(f"  wrote map: {map_path}")


def _no_distance(calculation: DistanceCalculation) -> RuntimeError:
    filter_label = _filter_label(calculation.property)
    return RuntimeError(
        f"{calculation.output}: no finite positive distance exists for filter {filter_label!r}."
    )


def run(config: DistanceConfig, case: Any) -> int:
    output_dir = Path.cwd().resolve()
    fault_names = {
        calculation.name
        for calculation in config.distance_calculations
        if calculation.type == "fault"
    }
    grid = case.grid(_GRID_INDEX)
    size = grid.dimensions()
    dimensions: _Dimensions = size.i, size.j, size.k
    total_cells = math.prod(dimensions)
    if not total_cells:
        raise RuntimeError("The grid contains no cell centers.")
    active_indices = {
        _flat_index(info.local_ijk, dimensions)
        for info in case.cell_info_for_active_cells()
        if info.grid_index == _GRID_INDEX
    }
    step_dates = [date(step.year, step.month, step.day) for step in case.time_steps()]
    cell_centers = cache(partial(_cell_centers, grid, total_cells))
    well_centers = cache(
        partial(
            _well_centers,
            case=case,
            cell_centers=cell_centers,
            dimensions=dimensions,
            report_count=len(step_dates),
        )
    )
    target_for = _make_target_lookup(
        case, fault_names, total_cells, cell_centers, well_centers
    )
    filter_cells = _make_cell_selector(case, active_indices, step_dates, total_cells)

    nx, ny, nz = dimensions
    print(
        f"Grid: {nx} x {ny} x {nz} = {total_cells} cells ({len(active_indices)} active)"
    )

    for calculation in config.distance_calculations:
        indices = filter_cells(calculation.property)
        verbose = config.verbose if calculation.verbose is None else calculation.verbose
        scalar_path = output_dir / calculation.output
        map_path = output_dir / f"{calculation.output}_map" if verbose else None
        result = _run_calculation(
            calculation, target_for, indices, scalar_path, map_path
        )
        well_connection_count = (
            len(well_centers(calculation.name)) if calculation.type == "well" else None
        )
        _report_calculation(
            calculation,
            len(indices),
            result,
            dimensions,
            scalar_path,
            map_path,
            well_connection_count=well_connection_count,
        )
    return 0
