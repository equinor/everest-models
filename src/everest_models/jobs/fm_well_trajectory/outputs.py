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


def write_guide_points(guide_points: Dict[str, Trajectory], filename: Path) -> None:
    io.dump_json(
        {
            well: [data.x.tolist(), data.y.tolist(), data.z.tolist()]
            for well, data in guide_points.items()
        },
        filename,
    )


def write_mlt_guide_points(guide_points: Dict[str, Trajectory], filename: Path) -> None:
    io.dump_json(
        {
            well: {
                branch: [
                    branch_data[1].x.tolist(),
                    branch_data[1].y.tolist(),
                    branch_data[1].z.tolist(),
                ]
                for branch, branch_data in well_data.items()
            }
            for well, well_data in guide_points.items()
        },
        filename,
    )


def write_mlt_guide_md(guide_points: Dict[str, Trajectory], filename: Path) -> None:
    io.dump_json(
        {
            well: {branch: branch_data[0] for branch, branch_data in well_data.items()}
            for well, well_data in guide_points.items()
        },
        filename,
    )


def write_well_costs(costs: Dict[str, float], npv_file: Path) -> None:
    output = io.load_yaml(npv_file)

    for well_cost in (
        entry for entry in output["well_costs"] if entry["well"] in costs
    ):
        well_cost["value"] = costs[well_cost["well"]]

    with npv_file.open("w") as fp:
        io.dump_yaml(output, fp, default_flow_style=False)
