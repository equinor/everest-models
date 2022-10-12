import logging

from spinningjenny import rescale_value, str2date

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
            n = round(
                rescale_value(
                    number_of_wells,
                    scaled_bounds[0],
                    scaled_bounds[1],
                    float(real_bounds[0]),
                    float(real_bounds[1]),
                ),
            )
        else:
            n = round(number_of_wells)

    wells = sorted(input_wells, key=lambda k: k["readydate"])

    if max_date is not None:
        wells = [well for well in wells if str2date(well["readydate"]) <= max_date]
        if number_of_wells is None or len(wells) < n:
            n = len(wells)

    if n > len(wells):
        raise ValueError(f"Too many wells requested ({n}).")

    return wells[:n]
