def entry_points():
    """
    Dictionary mapping a spinning jenny job name to it's main entry point script function.
    This dictionary is used when creating the runnable python entries. The spinningjenny
    module expects there is one entry point per config file and this constraint
    will be enforced using a test.
    :return:
    """
    return {
        "drill_planner": "spinningjenny.script.fm_drill_planner:main_entry_point",
        "npv": "spinningjenny.script.fm_npv:main_entry_point",
        "rf": "spinningjenny.script.fm_rf:main_entry_point",
        "schmerge": "spinningjenny.script.fm_schmerge:main_entry_point",
        "stea": "spinningjenny.script.fm_stea:main_entry_point",
        "strip_dates": "spinningjenny.script.fm_strip_dates:main_entry_point",
        "well_constraints": "spinningjenny.script.fm_well_constraints:main_entry_point",
        "add_templates": "spinningjenny.script.fm_add_templates:main_entry_point",
        "well_filter": "spinningjenny.script.fm_well_filter:main_entry_point",
        "interpret_well_drill": "spinningjenny.script.fm_interpret_well_drill:main_entry_point",
    }