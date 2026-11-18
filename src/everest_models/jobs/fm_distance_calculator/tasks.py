from __future__ import annotations

import math
import statistics
from collections.abc import Iterable, Sequence
from datetime import date
from pathlib import Path
from typing import Any

from everest_models.jobs.shared.resinsight import rips

from .config_model import DistanceCalculation, DistanceConfig, Point, PropertyFilter


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
    distances: Sequence[float], indices: Iterable[int], aggregation: str
) -> tuple[int | None, float | None]:
    if aggregation not in {"min", "max", "mean", "median"}:
        raise ValueError(
            f"Unsupported aggregation {aggregation!r}; expected min, max, mean, or median."
        )
    candidates = [
        (index, distances[index])
        for index in indices
        if math.isfinite(distances[index]) and distances[index] > 0.0
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


def run(config: DistanceConfig, case: Any) -> int:
    grid_index = 0
    output_dir = Path.cwd().resolve()

    def check_length(values: Sequence[Any], description: str) -> Sequence[Any]:
        if len(values) != total_cells:
            raise RuntimeError(
                f"Expected {total_cells} {description}, got {len(values)}."
            )
        return values

    def find_faults(fault_names: set[str]) -> tuple[Any, dict[str, list[Any]]]:
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

    fault_names = {
        calculation.name
        for calculation in config.distance_calculations
        if calculation.type == "fault"
    }
    if fault_names:
        view, fault_views = find_faults(fault_names)
    else:
        view, fault_views = None, {}

    grid = case.grid(grid_index)
    dimensions = grid.dimensions()
    nx, ny, nz = dimensions.i, dimensions.j, dimensions.k
    total_cells = nx * ny * nz
    cell_centers = check_length(grid.cell_centers(), "cell centers")
    if not cell_centers:
        raise RuntimeError("The grid contains no cell centers.")

    active_global_indices = set()
    for info in case.cell_info_for_active_cells():
        if info.grid_index != grid_index:
            continue
        ijk = info.local_ijk
        active_global_indices.add(ijk.i + ijk.j * nx + ijk.k * nx * ny)

    time_steps = case.time_steps()
    step_dates = [date(step.year, step.month, step.day) for step in time_steps]
    mean_center_z = sum(center.z for center in cell_centers) / len(cell_centers)
    depth_sign = -1.0 if mean_center_z < 0.0 else 1.0

    fault_distance_cache: dict[str, Sequence[float]] = {}
    well_distance_cache: dict[str, Sequence[float]] = {}
    well_connection_counts: dict[str, int] = {}
    polyline_distance_cache: dict[tuple[Point, ...], Sequence[float]] = {}
    mask_cache: dict[tuple[str, float, date | None], set[int]] = {}

    def fault_distances_for(fault_name: str) -> Sequence[float]:
        if fault_name not in fault_distance_cache:
            fault_distance = view.add_fault_distance(
                f"PY_FAULTDIST_{fault_name}", fault_views[fault_name]
            )
            fault_distance_cache[fault_name] = check_length(
                case.grid_property(
                    rips.PropertyType.GENERATED,
                    fault_distance.result_name,
                    0,
                    grid_index,
                ),
                f"{fault_name} fault distances",
            )
        return fault_distance_cache[fault_name]

    def well_distances_for(well_name: str) -> Sequence[float]:
        if well_name not in well_distance_cache:
            simulation_wells = case.simulation_wells()
            simulation_well = next(
                (well for well in simulation_wells if well.name == well_name), None
            )
            if simulation_well is None:
                raise RuntimeError(
                    f"Simulation well {well_name!r} not found. Available: "
                    f"{sorted(well.name for well in simulation_wells)}"
                )
            connected_global_indices = set()
            for time_step_index in range(len(time_steps)):
                for connection in simulation_well.cells(time_step_index):
                    if connection.grid_index != grid_index:
                        continue
                    ijk = connection.ijk
                    connected_global_indices.add(ijk.i + ijk.j * nx + ijk.k * nx * ny)
            if not connected_global_indices:
                raise RuntimeError(
                    f"Simulation well {well_name!r} has no connections in grid {grid_index}."
                )
            well_centers = [
                (cell_centers[index].x, cell_centers[index].y, cell_centers[index].z)
                for index in sorted(connected_global_indices)
            ]
            well_connection_counts[well_name] = len(connected_global_indices)
            well_distance_cache[well_name] = [
                min(
                    math.dist((center.x, center.y, center.z), well_center)
                    for well_center in well_centers
                )
                for center in cell_centers
            ]
        return well_distance_cache[well_name]

    def polyline_distances_for(points: tuple[Point, ...]) -> Sequence[float]:
        if points not in polyline_distance_cache:
            polyline = [
                (easting, northing, depth_sign * depth)
                for easting, northing, depth in points
            ]
            segments = list(zip(polyline, polyline[1:], strict=False))
            polyline_distance_cache[points] = [
                min(
                    point_to_segment_distance_3d(
                        (center.x, center.y, center.z), start, end
                    )
                    for start, end in segments
                )
                for center in cell_centers
            ]
        return polyline_distance_cache[points]

    def selected_cells(property_filter: PropertyFilter | None) -> tuple[set[int], str]:
        if property_filter is None:
            return active_global_indices, "all active cells (no 'property' set)"

        keyword = property_filter.name.upper()
        threshold = property_filter.threshold
        report_date = property_filter.date
        key = (keyword, threshold, report_date)
        if key not in mask_cache:
            if report_date is None:
                time_step_indices = list(range(len(step_dates)))
                if not step_dates:
                    raise RuntimeError(
                        "No report dates are available for dynamic property filtering."
                    )
            elif report_date not in step_dates:
                available_dates = [step.isoformat() for step in step_dates]
                raise RuntimeError(
                    f"Report date {report_date} not found. Available: {available_dates}"
                )
            else:
                time_step_indices = [step_dates.index(report_date)]

            matching_indices: set[int] = set()
            for time_step_index in time_step_indices:
                values = check_length(
                    case.grid_property(
                        rips.PropertyType.DYNAMIC_NATIVE,
                        keyword,
                        time_step_index,
                        grid_index,
                    ),
                    f"{keyword} values",
                )
                matching_indices.update(
                    index
                    for index in active_global_indices
                    if math.isfinite(values[index]) and values[index] >= threshold
                )
            mask_cache[key] = matching_indices
        return (
            mask_cache[key],
            f"{keyword} >= {threshold:g} @ {report_date or 'all timesteps'}",
        )

    def distances_for(calculation: DistanceCalculation) -> tuple[Sequence[float], str]:
        if calculation.type == "fault":
            fault_name = calculation.name
            return fault_distances_for(fault_name), f"fault {fault_name}"
        if calculation.type == "well":
            well_name = calculation.name
            return well_distances_for(well_name), f"well {well_name}"
        return (
            polyline_distances_for(calculation.points),
            f"polyline of {len(calculation.points)} points",
        )

    print(
        f"Grid: {nx} x {ny} x {nz} = {total_cells} cells "
        f"({len(active_global_indices)} active)"
    )
    for calculation in config.distance_calculations:
        output_name = calculation.output
        multiplier = calculation.multiplier
        aggregation = calculation.aggregation
        verbose = config.verbose if calculation.verbose is None else calculation.verbose
        distances, target_label = distances_for(calculation)
        indices, filter_label = selected_cells(calculation.property)
        index, distance = aggregate_distance(distances, indices, aggregation)
        if distance is None:
            raise RuntimeError(
                f"{output_name}: no finite positive distance exists for filter "
                f"{filter_label!r}."
            )

        scalar_path = output_dir / output_name
        if verbose:
            converted_distances = [value * multiplier for value in distances]
            write_property(
                [output_dir / f"{output_name}_map"], output_name, converted_distances
            )
        converted_distance = distance * multiplier
        write_scalar([scalar_path], converted_distance)

        print(f"\n{output_name}  ->  {target_label}")
        print(f"  filter: {filter_label} ({len(indices)} cells)")
        result = f"  {aggregation} distance: {converted_distance:.2f}"
        if multiplier != 1:
            result += f" (multiplied by {multiplier:g})"
        if index is not None:
            i = index % nx
            j = (index // nx) % ny
            k = index // (nx * ny)
            result += f" at ijk ({i + 1}, {j + 1}, {k + 1})"
        print(result)
        print(f"  wrote scalar: {scalar_path}")
        if verbose:
            print(f"  wrote map: {output_dir / f'{output_name}_map'}")

    for well_name, count in sorted(well_connection_counts.items()):
        print(f"\nUnique {well_name} connection cells: {count}")
    return 0
