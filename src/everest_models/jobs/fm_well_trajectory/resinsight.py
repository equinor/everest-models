import datetime
import logging
from pathlib import Path
from typing import Any, Dict, Iterable, Optional, Tuple, Union

import lasio
import pandas
import rips

from everest_models.jobs.shared.models.phase import PhaseEnum

from .models.config import (
    ConnectionConfig,
    DynamicDomainProperty,
    PerforationConfig,
    StaticDomainProperty,
    WellConfig,
)
from .models.data_structs import Trajectory

logger = logging.getLogger(__name__)


def _create_perforation_view(
    perforations: Iterable[PerforationConfig],
    formations_file: Path,
    case: rips.Case,
    well_name: str,
) -> None:
    perforation = next((item for item in perforations if item.well == well_name), None)
    if perforation is not None and perforation.formations:
        case.import_formation_names([bytes(formations_file.resolve())])
    case.create_view().set_time_step(-1)


def read_wells(
    project: rips.Project,
    well_path_folder: Path,
    well_names: Iterable[str],
    connection: Optional[ConnectionConfig],
) -> None:
    project.import_well_paths(
        well_path_files=[
            str(well_path_folder / f"{well_name}.dev") for well_name in well_names
        ],
        well_path_folder=str(well_path_folder),
    )

    if connection is not None:
        for well_name in well_names:
            _create_perforation_view(
                connection.perforations,
                connection.formations_file,
                project.cases()[0],
                well_name,
            )

    project.update()


def create_well(
    connection: ConnectionConfig,
    well_config: WellConfig,
    guide_points: Trajectory,
    project: rips.Project,
) -> Any:
    _create_perforation_view(
        connection.perforations,
        connection.formations_file,
        project.cases()[0],
        well_config.name,
    )

    well_path_collection = project.descendants(rips.WellPathCollection)[0]
    well_path = well_path_collection.add_new_object(rips.ModeledWellPath)
    well_path.name = well_config.name
    well_path.update()

    geometry = well_path.well_path_geometry()
    reference_point = geometry.reference_point
    reference_point[0] = str(guide_points.x[0])
    reference_point[1] = str(guide_points.y[0])
    reference_point[2] = str(guide_points.z[0])
    geometry.update()

    intersection_points = []
    for point in zip(guide_points.x[1:], guide_points.y[1:], guide_points.z[1:]):
        coord = [str(item) for item in point]
        target = geometry.append_well_target(coordinate=coord, absolute=True)
        target.dogleg1 = well_config.dogleg
        target.dogleg2 = well_config.dogleg
        target.update()
        intersection_points.append(coord)
    geometry.update()

    intersection_collection = project.descendants(rips.IntersectionCollection)[0]
    intersection = intersection_collection.add_new_object(rips.CurveIntersection)
    intersection.points = intersection_points
    intersection.update()

    for well in geometry.well_path_targets():
        logger.info(
            "\t".join(
                (
                    f"DL1: {well.dogleg1}",
                    f"DL2: {well.dogleg2}",
                    f"Azi: {well.azimuth}",
                    f"Incl: {well.inclination}",
                )
            )
        )

    return well_path


def create_branches(
    well_config: WellConfig,
    well_path: Any,
    mlt_guide_points: Dict[str, Tuple[float, Trajectory]],
    project: rips.Project,
) -> Any:
    for md, guide_points in mlt_guide_points.values():
        lateral = well_path.append_lateral(md)
        geometry = lateral.well_path_geometry()

        intersection_points = []
        for point in zip(guide_points.x[1:], guide_points.y[1:], guide_points.z[1:]):
            coord = [str(item) for item in point]
            target = geometry.append_well_target(coordinate=coord, absolute=True)
            target.dogleg1 = well_config.dogleg
            target.dogleg2 = well_config.dogleg
            target.update()
            intersection_points.append(coord)
        geometry.update()

        intersection_collection = project.descendants(rips.IntersectionCollection)[0]
        intersection = intersection_collection.add_new_object(rips.CurveIntersection)
        intersection.points = intersection_points
        intersection.update()


def _find_time_step(
    case: rips.Case, date: Optional[datetime.date] = None
) -> Optional[int]:
    time_step_num = None
    time_steps = case.time_steps()
    for ts_idx, time_step in enumerate(time_steps):
        date_simgrid = datetime.date(time_step.year, time_step.month, time_step.day)
        if date_simgrid == date:
            time_step_num = ts_idx
            logger.info(f"Timestep number for the date {date_simgrid}: {time_step_num}")
            break
    return time_step_num


def _create_tracks(
    properties: Iterable[str],
    property_type: str,
    case: rips.Case,
    well_path: rips.WellPath,
    well_log_plot: rips.WellLogPlot,
    time_step_num: Optional[int] = None,
) -> None:
    for property in properties:
        track = well_log_plot.new_well_log_track(f"Track: {property}", case, well_path)
        track.add_extraction_curve(
            case, well_path, property_type, property, time_step_num
        )


def create_well_logs(
    perforations: Iterable[PerforationConfig],
    project: rips.Project,
    eclipse_model: Path,
    project_path: Path,
    date: Optional[datetime.date],
) -> None:
    case = project.cases()[0]

    well_log_plot_collection = project.descendants(rips.WellLogPlotCollection)[0]

    for well_path in project.well_paths():
        logger.info(f"Well name: {well_path.name}")

        well_log_plot = well_log_plot_collection.new_well_log_plot(case, well_path)

        # If we created multi-lateral wells, the well path names are stored in
        # the form "name Y#", e.g., "INJ Y1", where the index Y# indicates the
        # number of the branch, and Y1 is the main trajectory. We need to split
        # and take the first part to get the original well name:
        well_name_base = well_path.name.partition(" Y")[0].strip()

        perforation = next(item for item in perforations if item.well == well_name_base)

        if perforation.dynamic:
            restart = eclipse_model.with_suffix(".UNRST")
            if not restart.is_file():
                raise RuntimeError(
                    f"Dynamic perforations specified, but {restart} file not found. "
                )
            _create_tracks(
                perforation.dynamic,
                "DYNAMIC_NATIVE",
                case,
                well_path,
                well_log_plot,
                _find_time_step(case, date),
            )
        if perforation.static:
            _create_tracks(
                perforation.static,
                "STATIC_NATIVE",
                case,
                well_path,
                well_log_plot,
                0,
            )
        if perforation.formations:
            property_name = "Active Formation Names"
            track = well_log_plot.new_well_log_track(
                f"Track: {property_name}", case, well_path
            )
            track.add_extraction_curve(
                case, well_path, "FORMATION_NAMES", property_name, 0
            )

        logger.info(
            "Calling 'export_data_as_las' on the resinsight project with"
            f"'export_folder={project_path}'\ncwd = {Path.cwd()}"
        )
        well_log_plot.export_data_as_las(export_folder=str(project_path))

    project.update()


def _filter_properties(
    conditions: pandas.Series,
    df: pandas.DataFrame,
    properties: Tuple[Union[DynamicDomainProperty, StaticDomainProperty], ...],
) -> pandas.Series:
    for property in properties:
        if property.min is not None:
            conditions = conditions & (df[property.key] > property.min)
        if property.max is not None:
            conditions = conditions & (df[property.key] < property.max)
    return conditions


def _select_perforations(
    perforation: PerforationConfig, df: pandas.DataFrame
) -> Tuple[pandas.Series, Optional[float]]:
    well_depth = df["DEPTH"].max()
    logger.info(f"Well total measured depth: {well_depth}")

    if not df.empty:
        return (
            _filter_perforation_properties(perforation, df, df["DEPTH"] > 0.0),
            well_depth,
        )
    logger.warning("Well log empty")
    return df["DEPTH"], None


def _filter_perforation_properties(
    perforation: PerforationConfig, df: pandas.DataFrame, conditions: pandas.Series
):
    # Filter formations
    if perforation.formations:
        conditions = df["ACTIVE_FORMATION_NAMES"].isin(perforation.formations)

    # Filter dynamic and static properties
    conditions = _filter_properties(conditions, df, perforation.dynamic)
    conditions = _filter_properties(conditions, df, perforation.static)

    df_selected = df.loc[conditions]
    df_selected.describe().loc[["min", "max"]]

    return df_selected["DEPTH"]


def _read_las_file(las: Path) -> pandas.DataFrame:
    return lasio.read(las).df().reset_index()


def make_perforations(
    project: rips.Project,
    well_name: str,
    perforations: Iterable[PerforationConfig],
    wells: Iterable[WellConfig],
    path: Path,
):
    # If we created multi-lateral wells, the well path names are stored in the
    # form "name Y#", e.g., "INJ Y1", where the index Y# indicates the number of
    # the branch, and Y1 is the main trajectory. We need to split and take the
    # first part to get the original well name:
    well_name_base = well_name.partition(" Y")[0].strip()

    perf_depths, well_depth = _select_perforations(
        perforation=next(item for item in perforations if item.well == well_name_base),
        df=_read_las_file(next(path.glob(f"{well_name.replace(' ', '_')}*.las"))),
    )
    well = next(item for item in wells if item.name == well_name_base)

    export_filename: Optional[Path] = None

    if well_depth is not None:
        well_path = project.well_path_by_name(well_name)
        total_perf_length = 0
        if perf_depths.size > 0:
            for start, end in zip(perf_depths.iloc[::2], perf_depths.iloc[1::2]):
                well_path.append_perforation_interval(
                    start_md=start,
                    end_md=end,
                    diameter=2 * well.radius,
                    skin_factor=well.skin,
                )
                total_perf_length = round(total_perf_length + end - start, 2)
            logger.info(f"Total perforation length is {total_perf_length}")
        else:  # create one dummy connection and shut it afterwards:
            well_path.append_perforation_interval(
                start_md=well_depth - 1,
                end_md=well_depth,
                diameter=2 * well.radius,
                skin_factor=well.skin,
            )

        export_filename = (path / well_name.replace(" ", "_")).with_suffix(".SCH")
        logger.info(
            f"Exporting well completion data to: {export_filename}"
            f"\ncwd = {Path.cwd()}"
        )
        project.cases()[0].export_well_path_completions(
            time_step=0,
            well_path_names=[well_path.name],
            file_split="UNIFIED_FILE",
            include_perforations=True,
            export_comments=False,
            custom_file_name=str(export_filename),
        )

    if export_filename is not None:
        _generate_welspecs(
            well.name, well.phase, well.group, export_filename, perf_depths, path
        )

    project.update()
    return None if well_depth is None else well


def _generate_welspecs(
    well: str,
    phase: PhaseEnum,
    group: str,
    export_filename: Path,
    perf_depths: pandas.Series,
    project_path: Path,
) -> None:
    #### edit well group name in WELSPECS in the exported schedule file
    #### this currently is not available in ResInsight Python API

    logger.info(f"Exporting well specs to: {export_filename}" f"\ncwd = {Path.cwd()}")

    if export_filename.is_file():
        with open(export_filename, "r") as file_obj:
            lines = file_obj.readlines()

        with open(export_filename, "w") as file_obj:
            for idx, line in enumerate(lines):
                if line.startswith("WELSPECS"):
                    lines[idx + 1] = lines[idx + 1].replace(
                        lines[idx + 1].split()[1], group, 1
                    )
                    logger.info(f"Group name for the well is set to: {group}")

                    lines[idx + 1] = lines[idx + 1].replace(
                        lines[idx + 1].split()[5], phase.value, 1
                    )
                    logger.info(f"Phase name for the well is set to: {phase.value}")

                if line.startswith("COMPDAT") and perf_depths.size == 0:
                    comment = (
                        "-- No interval found that meets the defined perf criteria; "
                        "create one dummy connection and shut it thereafter."
                    )
                    lines[idx + 1] = comment + lines[idx + 1].replace(
                        lines[idx + 1].split()[5], "SHUT"
                    )
                    logger.info(comment)
                file_obj.write(line)
    else:
        logger.info("Well outside of the grid. Creating dummy shut connection.")
        # write dummy WELSPECS and COMPDAT:
        dummy = [
            "-- WELL  GROUP           BHP    PHASE  DRAIN  INFLOW  OPEN  CROSS  PVT    HYDS  FIP \n",
            "-- NAME  NAME   I    J   DEPTH  FLUID  AREA   EQUANS  SHUT  FLOW   TABLE  DENS  REGN \n",
            "WELSPECS \n",
            f"   {well}  {group}     1  1  1*     {phase.value}    0.0    STD     STOP  YES    0      SEG   0    / \n ",
            "    / \n",
            "-- WELL                        OPEN   SAT   CONN           WELL      KH             SKIN      D      DIR \n",
            "-- NAME   I     J    K1   K2   SHUT   TAB   FACT           DIA       FACT           FACT      FACT   PEN \n",
            "COMPDAT \n",
            f"   {well}   1   1   1   1   SHUT   1*    1   0.21600   1   0.00000   1*     'Z' / \n",
            "  /  \n",
        ]
        with open(export_filename, "w") as file_obj:
            file_obj.writelines(dummy)

        # Write dummy WELSEGS and COMPSEGS:
        dummy = ["WELSEGS \n", "/ \n", "COMPSEGS \n", "/ \n"]
        export_filename = (project_path / (well + "_MSW")).with_suffix(".SCH")
        with open(export_filename, "w") as file_obj:
            file_obj.writelines(dummy)
