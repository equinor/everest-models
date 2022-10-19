import datetime
import logging

from spinningjenny.jobs.utils.converters import rescale_value

logger = logging.getLogger(__name__)


def select_wells(
    input_wells, number_of_wells, real_bounds=None, scaled_bounds=None, max_date=None
):

    if number_of_wells is not None:
        if real_bounds is not None and scaled_bounds is not None:
            if real_bounds[1] < real_bounds[0]:
                raise ValueError(
                    f"Invalid real bounds: [{real_bounds[0]}, {real_bounds[1]}]"
                )
            if scaled_bounds[1] < scaled_bounds[0]:
                raise ValueError(
                    f"Invalid scaled bounds: [{scaled_bounds[0]}, {scaled_bounds[1]}]"
                )
            # We need to map the controls to the user-specified range of
            # integers. Extend the user bounds each with 0.5, rounding will then
            # select integers from equidistant ranges in the control space:
            n = round(
                rescale_value(
                    number_of_wells,
                    scaled_bounds[0],
                    scaled_bounds[1],
                    float(real_bounds[0]) - 0.5,
                    float(real_bounds[1]) + 0.5,
                ),
            )
            # When near the bounds we can happen to round to the previous or
            # next integer, fix that:
            n = max(real_bounds[0], min(n, real_bounds[1]))
        else:
            n = round(number_of_wells)

    wells = sorted(input_wells, key=lambda k: k["readydate"])

    if max_date is not None:
        wells = [
            well
            for well in wells
            if datetime.date.fromisoformat(well["readydate"]) <= max_date
        ]
        if number_of_wells is None or len(wells) < n:
            n = len(wells)

    if n > len(wells):
        raise ValueError(f"Too many wells requested ({n}).")

    return wells[:n]
