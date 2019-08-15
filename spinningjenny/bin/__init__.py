def entry_points():
    return [
        "fm_drill_planner = spinningjenny.script.drill_planner:main_entry_point",
        "fm_npv = spinningjenny.script.npv:main_entry_point",
        "fm_rf = spinningjenny.script.rf:main_entry_point",
        "fm_schmerge = spinningjenny.script.schmerge:main_entry_point",
        "fm_stea = spinningjenny.script.stea_fmu:main_entry_point",
        "fm_strip_dates = spinningjenny.script.strip_dates:main_entry_point",
        "fm_well_constraints = spinningjenny.script.well_constraints:main_entry_point",
        "fm_add_templates = spinningjenny.script.add_templates:main_entry_point",
        "fm_well_filter = spinningjenny.script.well_filter:main_entry_point",
        "fm_interpret_well_drill = spinningjenny.script.interpret_well_drill:main_entry_point",
    ]
