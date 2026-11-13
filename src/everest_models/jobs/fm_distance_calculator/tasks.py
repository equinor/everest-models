from __future__ import annotations

import math
import statistics
from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import Any

from everest_models.jobs.shared.resinsight import rips


def normalize_config(config: dict[str, Any]) -> dict[str, Any]:
    def normalize_mapping(mapping: dict[str, Any], context: str) -> dict[str, Any]:
        normalized = {}
        original_keys = {}
        for key, value in mapping.items():
            normalized_key = key.replace("-", "_") if isinstance(key, str) else key
            if normalized_key in normalized:
                raise ValueError(
                    f"{context}: conflicting spellings for key "
                    f"'{normalized_key}': '{original_keys[normalized_key]}' and '{key}'"
                )
            normalized[normalized_key] = value
            original_keys[normalized_key] = key
        return normalized

    normalized = normalize_mapping(config, "Config")
    calculations = normalized.get("distance_calculations")
    if isinstance(calculations, list):
        normalized_calculations = []
        for index, calculation in enumerate(calculations, start=1):
            if isinstance(calculation, dict):
                calculation = normalize_mapping(
                    calculation, f"Distance calculation #{index}"
                )
                if isinstance(calculation.get("type"), str):
                    calculation["type"] = calculation["type"].replace("-", "_")
            normalized_calculations.append(calculation)
        normalized["distance_calculations"] = normalized_calculations
    return normalized


def config_values(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    if isinstance(value, (list, tuple)):
        return [str(item).strip() for item in value if str(item).strip()]
    return [str(value).strip()]


def parse_polygon_point(point: Any) -> tuple[float, float, float]:
    values = config_values(point)
    if len(values) != 3:
        raise ValueError(
            "Each polygon_input point must contain easting, northing, and depth: "
            f"{point!r}"
        )
    return tuple(float(value) for value in values)


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


def _resolve_unit_conversion(calculation: dict[str, Any], context: str) -> float:
    conversion_keys = {"unit-conversion", "unit_conversion"} & calculation.keys()
    if len(conversion_keys) > 1 or (conversion_keys and "u" in calculation):
        raise ValueError(f"{context}: use either 'unit-conversion' or 'u', not both")
    value = calculation.get(
        "unit-conversion", calculation.get("unit_conversion", calculation.get("u"))
    )
    try:
        conversion = float(1.0 if value is None else value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{context}: unit-conversion must be numeric") from error
    if conversion == 0:
        raise ValueError(f"{context}: unit-conversion must be non-zero")
    return conversion


def run(config: dict[str, Any], case: Any) -> int:
    config = normalize_config(config)
    calculations = config.get("distance_calculations") or []
    if not calculations:
        raise ValueError("No 'distance_calculations' entries found in the YAML config.")
    if not isinstance(calculations, list) or not all(
        isinstance(calculation, dict) for calculation in calculations
    ):
        raise ValueError("'distance_calculations' must be a list of mappings.")
    default_printing_distance_map = config.get("printing_distance_map", False)
    if not isinstance(default_printing_distance_map, bool):
        raise ValueError("'printing_distance_map' must be a boolean.")

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
        calculation["fault_name"]
        for calculation in calculations
        if calculation.get("type") == "fault_distance"
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
    step_dates = [
        f"{step.year:04d}-{step.month:02d}-{step.day:02d}" for step in time_steps
    ]
    mean_center_z = sum(center.z for center in cell_centers) / len(cell_centers)
    depth_sign = -1.0 if mean_center_z < 0.0 else 1.0

    fault_distance_cache: dict[str, Sequence[float]] = {}
    well_distance_cache: dict[str, Sequence[float]] = {}
    well_connection_counts: dict[str, int] = {}
    polyline_distance_cache: dict[tuple[Any, ...], Sequence[float]] = {}
    mask_cache: dict[tuple[str, float, str], set[int]] = {}

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

    def polyline_distances_for(
        points: Sequence[tuple[float, float, float]],
    ) -> Sequence[float]:
        key = tuple(points)
        if key not in polyline_distance_cache:
            polyline = [
                (easting, northing, depth_sign * depth)
                for easting, northing, depth in points
            ]
            segments = list(zip(polyline, polyline[1:], strict=False))
            if not segments:
                raise ValueError("polygon_input needs at least two points.")
            polyline_distance_cache[key] = [
                min(
                    point_to_segment_distance_3d(
                        (center.x, center.y, center.z), start, end
                    )
                    for start, end in segments
                )
                for center in cell_centers
            ]
        return polyline_distance_cache[key]

    def indices_for_triplet(
        keyword: str, property_threshold: float, output_date: str | None
    ) -> set[int]:
        key = (keyword, property_threshold, output_date)
        if key not in mask_cache:
            if output_date is None:
                time_step_indices = range(len(step_dates))
                if not step_dates:
                    raise RuntimeError(
                        "No report dates are available for dynamic property filtering."
                    )
            elif output_date not in step_dates:
                raise RuntimeError(
                    f"Report date {output_date} not found. Available: {step_dates}"
                )
            else:
                time_step_indices = [step_dates.index(output_date)]

            matching_indices = set()
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
                    if math.isfinite(values[index])
                    and values[index] >= property_threshold
                )
            mask_cache[key] = matching_indices
        return mask_cache[key]

    def selected_cells(calculation: dict[str, Any]) -> tuple[set[int], str]:
        properties = config_values(calculation.get("property"))
        if not properties:
            label = "all active cells (no 'property' set)"
            if config_values(calculation.get("output_date")):
                label += " - 'output_date' ignored without a 'property'"
            return active_global_indices, label

        thresholds = [
            float(value)
            for value in config_values(calculation.get("property_threshold"))
        ] or [0.0]
        output_dates = config_values(calculation.get("output_date"))

        triplets = []
        for position, keyword in enumerate(properties):
            triplet = (
                keyword.upper(),
                thresholds[min(position, len(thresholds) - 1)],
                output_dates[min(position, len(output_dates) - 1)]
                if output_dates
                else None,
            )
            if triplet not in triplets:
                triplets.append(triplet)
        indices = None
        for keyword, threshold, output_date in triplets:
            matched = indices_for_triplet(keyword, threshold, output_date)
            indices = matched if indices is None else indices & matched
        label = " & ".join(
            f"{keyword} >= {threshold:g} @ {output_date or 'all timesteps'}"
            for keyword, threshold, output_date in triplets
        )
        return indices or set(), label

    def distances_for(calculation: dict[str, Any]) -> tuple[Sequence[float], str]:
        kind = calculation.get("type")
        if kind == "fault_distance":
            fault_name = calculation["fault_name"]
            return fault_distances_for(fault_name), f"fault {fault_name}"
        if kind == "well_distance":
            well_name = calculation["well_name"]
            return well_distances_for(well_name), f"well {well_name}"
        if kind == "polygon_distance":
            points = [
                parse_polygon_point(point)
                for point in calculation.get("polygon_input", [])
            ]
            return polyline_distances_for(points), f"polyline of {len(points)} points"
        raise ValueError(f"Unsupported calculation type: {kind!r}")

    print(
        f"Grid: {nx} x {ny} x {nz} = {total_cells} cells "
        f"({len(active_global_indices)} active)"
    )
    for calculation in calculations:
        output_name = calculation.get("output_name")
        if not isinstance(output_name, str) or not output_name.strip():
            raise ValueError(
                "Each distance calculation requires a non-empty 'output_name'."
            )
        unit_conversion = _resolve_unit_conversion(calculation, output_name)
        aggregation = str(calculation.get("aggregation", "min")).strip().lower()
        printing_distance_map = calculation.get(
            "printing_distance_map", default_printing_distance_map
        )
        if not isinstance(printing_distance_map, bool):
            raise ValueError(
                f"{output_name}: 'printing_distance_map' must be a boolean."
            )
        distances, target_label = distances_for(calculation)
        indices, filter_label = selected_cells(calculation)
        index, distance = aggregate_distance(distances, indices, aggregation)
        if distance is None:
            raise RuntimeError(
                f"{output_name}: no finite positive distance exists for filter "
                f"{filter_label!r}."
            )

        scalar_path = output_dir / output_name
        if printing_distance_map:
            converted_distances = [value / unit_conversion for value in distances]
            write_property(
                [output_dir / f"{output_name}_map"], output_name, converted_distances
            )
        converted_distance = distance / unit_conversion
        write_scalar([scalar_path], converted_distance)

        print(f"\n{output_name}  ->  {target_label}")
        print(f"  filter: {filter_label} ({len(indices)} cells)")
        result = f"  {aggregation} distance: {converted_distance:.2f}"
        if unit_conversion != 1:
            result += f" (divided by {unit_conversion:g})"
        if index is not None:
            i = index % nx
            j = (index // nx) % ny
            k = index // (nx * ny)
            result += f" at ijk ({i + 1}, {j + 1}, {k + 1})"
        print(result)
        print(f"  wrote scalar: {scalar_path}")
        if printing_distance_map:
            print(f"  wrote map: {output_dir / f'{output_name}_map'}")

    for well_name, count in sorted(well_connection_counts.items()):
        print(f"\nUnique {well_name} connection cells: {count}")
    return 0
