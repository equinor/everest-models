from jobs.utils.converters import rescale_value


def drill_date_planner(wells, controls, bounds, max_days):
    if bounds[1] < bounds[0]:
        raise ValueError(f"Invalid bounds: [{bounds[0]}, {bounds[1]}]")
    if max_days <= 0:
        raise ValueError("max-days must be > 0")

    drill_times = {well["name"]: well["drill_time"] for well in wells}

    new_drill_times = {}
    for control_name, control_value in controls.items():
        if control_name not in drill_times:
            raise RuntimeError(f"Drill time missing for well: {control_name}")
        new_drill_times[control_name] = (
            int(rescale_value(control_value, bounds[0], bounds[1], 0.0, max_days))
            + drill_times[control_name]
        )

    for well in wells:
        if well["name"] not in new_drill_times:
            raise RuntimeError(f"Missing well in controls: {well['name']}")
        well["drill_time"] = new_drill_times[well["name"]]

    return wells
