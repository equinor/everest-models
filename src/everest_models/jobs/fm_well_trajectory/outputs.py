import csv
import math
from pathlib import Path
from typing import Dict, Iterable, Tuple

from everest_models.jobs.shared import io_utils as io

from .models.config import WellConfig
from .models.data_structs import CalculatedTrajectory, Trajectory


def join_float_values(*values) -> str:
    return "\t".join(f"{arg:f}" for arg in values)


def write_wicalc(
    wells: Dict[str, WellConfig],
    results: Dict[str, CalculatedTrajectory],
    path: Path,
) -> None:
    with path.open("w", encoding="utf-8") as file_obj:
        file_obj.writelines(
            f"{well}\t"
            + join_float_values(
                *(coordinate[idx] for coordinate in result.coordinates),
                *(coordinate[idx + 1] for coordinate in result.coordinates),
                result.length[idx],
                result.length[idx + 1],
                wells[well].radius,
                wells[well].skin,
            )
            + "\n"
            for well, result in results.items()
            for idx, _ in enumerate(result.coordinates.x[:-1])
        )


def write_resinsight(results: Dict[str, CalculatedTrajectory]) -> None:
    Path("wellpaths").mkdir(exist_ok=True)
    for well, result in results.items():
        with open(f"wellpaths/{well}.dev", "w", encoding="utf-8") as file_obj:
            file_obj.write(f"WELLNAME {well}\n")
            xs, ys, zs = result.coordinates
            for idx in range(len(xs)):
                file_obj.write(f"{xs[idx]:<24.4f}")
                file_obj.write(f"{ys[idx]:<24.4f}")
                file_obj.write(f"{zs[idx]:<24.4f}")
                file_obj.write(f"{result.length[idx]:.4f}\n")
            file_obj.write("-999\n")


def write_path_files(results: Iterable[Tuple[Path, CalculatedTrajectory]]) -> None:
    def f180(a: float) -> float:
        return a * 180 / math.pi

    for well, result in results:
        with well.open("w", encoding="utf-8") as file_obj:
            file_obj.writelines(
                join_float_values(
                    result.length[idx],
                    *(coordinate[idx] for coordinate in result.coordinates),
                    *(deviation[idx] for deviation in result.deviation),
                    f if (f := f180(result.azimuth[idx])) >= 0 else (f + 360),
                    f180(result.inclination[idx]),
                    result.dogleg[idx],
                )
                + "\n"
                for idx, _ in enumerate(result.coordinates.x)
            )


def _csv_writer(path: Path, guide_points: Dict[str, Trajectory]):
    with path.open("w", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file, delimiter=";", lineterminator="\n")
        writer.writerow(["well", "x", "y", "z"])
        writer.writerows(
            [well, x, y, z]
            for well, data in guide_points.items()
            for x, y, z in zip(data.x, data.y, data.z)
        )


def _json_writer(path: Path, guide_points: Dict[str, Trajectory]):
    io.dump_json(
        {
            well: [data.x.tolist(), data.y.tolist(), data.z.tolist()]
            for well, data in guide_points.items()
        },
        path,
    )


def write_guide_points(guide_points: Dict[str, Trajectory], filename: Path) -> None:
    if writer := {".csv": _csv_writer, ".json": _json_writer}.get(filename.suffix):
        writer(filename, guide_points)
    else:
        raise RuntimeError("guide points file format not supported")


def write_well_costs(costs: Dict[str, float], npv_file: Path) -> None:
    output = io.load_yaml(npv_file)

    for well_cost in (
        entry for entry in output["well_costs"] if entry["well"] in costs
    ):
        well_cost["value"] = costs[well_cost["well"]]

    with npv_file.open("w") as fp:
        io.dump_yaml(output, fp, default_flow_style=False)
