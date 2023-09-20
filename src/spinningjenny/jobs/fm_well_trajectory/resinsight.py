import datetime
import logging
from pathlib import Path
from typing import Iterable, Optional, Tuple

import lasio
import pandas
import rips

from spinningjenny.jobs.shared.models.phase import PhaseEnum

from .models.config import (
    DomainProperty,
    PerforationConfig,
    PlatformConfig,
    ResInsightConnectionConfig,
    WellConfig,
)
from .models.data_structs import Trajectory

logger = logging.getLogger(__name__)


def _create_perforation_view(
    perforations: Iterable[PerforationConfig],
    formations_file: Path,
    case: rips.Case,
    wells: Iterable[str],
) -> None:
    for perforation in perforations:
        if perforation.well in wells:
            if perforation.formations:
                case.import_formation_names([bytes(formations_file.resolve())])
            case.create_view().set_time_step(-1)


def read_wells(
    project: rips.Project,
    well_path_folder: Path,
    well_names: Iterable[str],
    connection: Optional[ResInsightConnectionConfig],
) -> rips.Project:
    project.import_well_paths(
        well_path_files=[
            str(well_path_folder / f"{well_name}.dev") for well_name in well_names
        ],
        well_path_folder=str(well_path_folder),
    )
    if connection is not None:
        _create_perforation_view(
            connection.perforations,
            connection.formations_file,
            project.cases()[0],
            well_names,
        )

    project.update()

    return project


def create_well(
    connection: ResInsightConnectionConfig,
    platforms: Iterable[PlatformConfig],
    measured_depth_step: float,
    well: WellConfig,
    trajectory: Trajectory,
    project: rips.Project,
    project_path: Path,
) -> rips.Project:
    # ResInsight starts in a different directory we cannot use a relative path:
    project_file = project_path / "model.rsp"

    targets = [
        [str(x), str(y), str(z)]
        for x, y, z in zip(trajectory.x, trajectory.y, trajectory.z)
    ]

    _create_perforation_view(
        connection.perforations,
        connection.formations_file,
        project.cases()[0],
        well.name,
    )

    # Add a new modeled well path
    well_path_coll = project.descendants(rips.WellPathCollection)[0]
    well_path = well_path_coll.add_new_object(rips.ModeledWellPath)
    well_path.name = well.name
    well_path.update()

    # Create well targets
    intersection_points = []
    geometry = well_path.well_path_geometry()

    # if the first point is already a platform:
    if targets[0][2] == str(0.0):
        # set first point as platform and remove from targets
        reference = targets[0]
        targets = targets[1:]
    # otherwise, if platform and kickoff are inputs:
    elif well.platform is not None:
        platform = next(item for item in platforms if item.name == well.platform)
        reference = [platform.x, platform.y, platform.z]
        targets = [reference] + targets
    # finally, when there is no platform info create platform directly above
    # first guide point
    else:
        reference = [targets[0][0], targets[0][1], 0]

    # Create reference point
    reference_point = geometry.reference_point
    reference_point[0] = reference[0]
    reference_point[1] = reference[1]
    reference_point[2] = reference[2]
    geometry.update()

    for target in targets:
        coord = target
        target = geometry.append_well_target(coordinate=coord, absolute=True)
        target.dogleg1 = well.dogleg
        target.dogleg2 = well.dogleg
        target.update()
        intersection_points.append(coord)
    geometry.update()

    #### currently only available in resinsightdev
    intersection_coll = project.descendants(rips.IntersectionCollection)[0]
    # Add a CurveIntersection and set coordinates for the polyline
    intersection = intersection_coll.add_new_object(rips.CurveIntersection)
    intersection.points = intersection_points
    intersection.update()

    # Read out estimated dogleg and azimuth/inclination for well targets
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

    # Save the project to file
    logger.info(f"Saving project to: {project_file}")
    project.save(str(project_file))
    logger.info(
        f"Calling 'export_well_paths' on the resinsight project" f"\ncwd = {Path.cwd()}"
    )
    # This log is deceving, it assumes that rips.Project().export_well_paths()
    # exports the file to current workig dircetory (cwd) which is not true.
    # pytest changes the working directory to '/tmp' but '.export_well_paths`
    # keeps exporting the file to the project root directory
    project.export_well_paths(well_paths=None, md_step_size=measured_depth_step)

    return project


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
    date: Optional[datetime.date] = None,
) -> rips.Project:
    case = project.cases()[0]

    well_log_plot_collection = project.descendants(rips.WellLogPlotCollection)[0]

    for well_path in project.well_paths():
        logger.info(f"Well name: {well_path.name}")

        well_log_plot = well_log_plot_collection.new_well_log_plot(case, well_path)

        perforation = next(item for item in perforations if item.well == well_path.name)

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

    return project


def _filter_properties(
    conditions: pandas.Series,
    df: pandas.DataFrame,
    properties: Tuple[DomainProperty, ...],
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


def _make_perforations(
    well: WellConfig,
    case,
    well_path,
    perf_depths: pandas.Series,
    well_depth: Optional[float],
    project_path: Path,
) -> None:
    export_filename = (project_path / well.name.replace(" ", "_")).with_suffix(".SCH")

    diameter = well.radius * 2
    skin_factor = well.skin

    if well_depth is not None:
        total_perf_length = 0
        if perf_depths.size > 0:
            for start, end in zip(perf_depths.iloc[::2], perf_depths.iloc[1::2]):
                well_path.append_perforation_interval(
                    start_md=start,
                    end_md=end,
                    diameter=diameter,
                    skin_factor=skin_factor,
                )

                total_perf_length = round(total_perf_length + end - start, 2)
            logger.info(f"Total perforation length is {total_perf_length}")

        else:  # create one dummy connection and shut it thereafter
            well_path.append_perforation_interval(
                start_md=well_depth - 1,
                end_md=well_depth,
                diameter=diameter,
                skin_factor=skin_factor,
            )

        logger.info(
            f"Exporting well completion data to: {export_filename}"
            f"\ncwd = {Path.cwd()}"
        )
        case.export_well_path_completions(
            time_step=0,
            well_path_names=[well_path.name],
            file_split="UNIFIED_FILE",
            include_perforations=True,
            export_comments=False,
            custom_file_name=str(export_filename),
        )

    _generate_welspecs(
        well.name, well.phase, well.group, export_filename, perf_depths, project_path
    )


def _read_las_file(las: Path) -> pandas.DataFrame:
    return lasio.read(las).df().reset_index()


def make_perforations(
    project: rips.Project,
    well_name: str,
    perforations: Iterable[PerforationConfig],
    wells: Iterable[WellConfig],
    path: Path,
):
    perforation_depth, well_depth = _select_perforations(
        perforation=next(item for item in perforations if item.well == well_name),
        df=_read_las_file(next(path.glob(f"{well_name.replace(' ', '_')}*.las"))),
    )
    well = next(item for item in wells if item.name == well_name)
    _make_perforations(
        well=well,
        case=project.cases()[0],
        well_path=project.well_path_by_name(well.name),
        perf_depths=perforation_depth,
        well_depth=well_depth,
        project_path=path,
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
                    logger.info(f"Phase name for the well is set to: {phase}")

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
        # write dummy WELSPECS and COMPDAT
        dummy = [
            "-- WELL  GROUP           BHP    PHASE  DRAIN  INFLOW  OPEN  CROSS  PVT    HYDS  FIP \n",
            "-- NAME  NAME   I    J   DEPTH  FLUID  AREA   EQUANS  SHUT  FLOW   TABLE  DENS  REGN \n",
            "WELSPECS \n",
            f"   {well}  {group}     1  1  1*     {phase}    0.0    STD     STOP  YES    0      SEG   0    / \n ",
            "    / \n",
            "-- WELL                        OPEN   SAT   CONN           WELL      KH             SKIN      D      DIR \n",
            "-- NAME   I     J    K1   K2   SHUT   TAB   FACT           DIA       FACT           FACT      FACT   PEN \n",
            "COMPDAT \n",
            f"   {well}   1   1   1   1   SHUT   1*    1   0.21600   1   0.00000   1*     'Z' / \n",
            "  /  \n",
        ]
        with open(export_filename, "w") as file_obj:
            file_obj.writelines(dummy)

        # TODO: create dummy MSW file as well
        dummy = ["WELSEGS \n", "/ \n", "COMPSEGS \n", "/ \n"]
        export_filename = (project_path / (well + "_MSW")).with_suffix(".SCH")
        with open(export_filename, "w") as file_obj:
            file_obj.writelines(dummy)
