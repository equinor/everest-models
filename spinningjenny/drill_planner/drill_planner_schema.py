import collections
import configsuite
from configsuite import MetaKeys as MK
from configsuite import types


@configsuite.validator_msg("Should have a valid combination")
def _valid_combination_exists(elem, context):
    rigs_with_well = set([rig for rig in context.rigs if elem in rig.wells])
    slots_with_well = set([slot.name for slot in context.slots if elem in slot.wells])
    valid_combinations = [
        set(rig.slots).intersection(slots_with_well) for rig in rigs_with_well
    ]

    return any(valid_combinations)


@configsuite.validator_msg("Should be a defined slot")
def _is_slot(elem, context):
    return elem in context.slot_names


@configsuite.validator_msg("Should be prioritized")
def _is_prioritized(elem, context):
    return elem in context.prioritized_wells


@configsuite.validator_msg("Is x positive")
def _is_positive(elem):
    return elem > 0


@configsuite.validator_msg("Is x not negative")
def _is_not_negative(elem):
    return elem >= 0


@configsuite.validator_msg("Date should be after defined start date")
def _is_within_time_period(elem, context):
    return context.start_date <= elem <= context.end_date


def extract_validation_context(configuration):
    rigs = configuration.rigs if configuration.rigs else ()

    well_names = (
        tuple([well.name for well in configuration.wells])
        if configuration.wells
        else ()
    )

    slot_names = (
        tuple([slot.name for slot in configuration.slots])
        if configuration.slots
        else ()
    )

    slots = configuration.slots if configuration.slots else ()

    prioritized_wells = (
        tuple([well_name for well_name, _ in configuration.wells_priority])
        if configuration.wells_priority
        else ()
    )

    Context = collections.namedtuple(
        "Context",
        ("rigs", "slots", "slot_names", "start_date", "end_date", "prioritized_wells"),
    )
    return Context(
        rigs,
        slots,
        slot_names,
        configuration.start_date,
        configuration.end_date,
        prioritized_wells,
    )


_rig_description = """
The rig section must consist of a list of rigs. Each rig must then specify
 which wells and which slots can be drilled at the given rig. It is possible
 to add time periods that the rig is unavailable as a list of start and stop
 dates. The unavailability keyword is optional.
"""

_rig_schema = {
    MK.Type: types.List,
    MK.Description: _rig_description,
    MK.Content: {
        MK.Item: {
            MK.Type: types.NamedDict,
            MK.Content: {
                "name": {MK.Type: types.String, MK.Description: "Name of the rig."},
                "wells": {
                    MK.Type: types.List,
                    MK.Description: "A list of well names representing the wells that can be drilled from this rig.",
                    MK.Content: {
                        MK.Item: {
                            MK.Type: types.String,
                            MK.ContextValidators: (_valid_combination_exists,),
                        }
                    },
                },
                "slots": {
                    MK.Type: types.List,
                    MK.Description: "A list of slot names representing the slots that can be used from this rig.",
                    MK.Content: {
                        MK.Item: {
                            MK.Type: types.String,
                            MK.ContextValidators: (_is_slot,),
                        }
                    },
                },
                "unavailability": {
                    MK.Type: types.List,
                    MK.Description: "A list of time intervals representing periods that the rig is unavailable for drilling.",
                    MK.Content: {
                        MK.Item: {
                            MK.Type: types.NamedDict,
                            MK.Content: {
                                "start": {
                                    MK.Type: types.Date,
                                    MK.Description: "The start date for when the rig is unavailable. Must be ISO8601 formatted date",
                                    MK.ContextValidators: (_is_within_time_period,),
                                },
                                "stop": {
                                    MK.Type: types.Date,
                                    MK.Description: "The stop date for when the rig is unavailable. Must be ISO8601 formatted date",
                                    MK.ContextValidators: (_is_within_time_period,),
                                },
                            },
                        }
                    },
                },
                "delay": {
                    MK.Type: types.Integer,
                    MK.AllowNone: True,
                    MK.Description: (
                        "The number of days of preparation needed before the rig can start drilling a well. "
                        "This setting defaults to 0."
                    ),
                    MK.ElementValidators: (_is_not_negative,),
                },
            },
        }
    },
}

_slot_description = """
The slot section must consist of a list of slots. Each slot must then specify
 which wells can be drilled through the given slot. It is possible to add time
 periods that the slot is unavailable as a list of start and stop dates.
The unavailability keyword is optional.
"""

_slot_schema = {
    MK.Type: types.List,
    MK.Description: _slot_description,
    MK.Content: {
        MK.Item: {
            MK.Type: types.NamedDict,
            MK.Content: {
                "name": {MK.Type: types.String, MK.Description: "Name of the rig."},
                "wells": {
                    MK.Type: types.List,
                    MK.Description: "A list of well names representing the wells that can be drilled through this slot.",
                    MK.Content: {
                        MK.Item: {
                            MK.Type: types.String,
                            MK.ContextValidators: (_valid_combination_exists,),
                        }
                    },
                },
                "unavailability": {
                    MK.Type: types.List,
                    MK.Description: "A list of time intervals representing periods that the slot is unavailable for drilling.",
                    MK.Content: {
                        MK.Item: {
                            MK.Type: types.NamedDict,
                            MK.Content: {
                                "start": {
                                    MK.Type: types.Date,
                                    MK.Description: "The start date for when the slot is unavailable. Must be ISO8601 formatted date",
                                    MK.ContextValidators: (_is_within_time_period,),
                                },
                                "stop": {
                                    MK.Type: types.Date,
                                    MK.Description: "The stop date for when the slot is unavailable. Must be ISO8601 formatted date",
                                    MK.ContextValidators: (_is_within_time_period,),
                                },
                            },
                        }
                    },
                },
            },
        }
    },
}

_well_description = """
A list of wells each given a unique name and a value for how long it takes to
 drill the well
"""

_well_schema = {
    MK.Type: types.List,
    MK.Description: _well_description,
    MK.Content: {
        MK.Item: {
            MK.Type: types.NamedDict,
            MK.Content: {
                "name": {
                    MK.Type: types.String,
                    MK.Description: "Well name",
                    MK.ContextValidators: (_is_prioritized,),
                },
                "drill_time": {
                    MK.Type: types.Integer,
                    MK.Description: "Drill time given in days",
                    MK.ElementValidators: (_is_positive,),
                },
            },
        }
    },
}


def build():
    return {
        MK.Type: types.NamedDict,
        MK.Content: {
            "start_date": {
                MK.Type: types.Date,
                MK.Description: "ISO8601 formatted date",
            },
            "end_date": {MK.Type: types.Date, MK.Description: "ISO8601 formatted date"},
            "wells": _well_schema,
            "wells_priority": {
                MK.Type: types.Dict,
                MK.Description: "A list of wells with a well priority value",
                MK.Content: {
                    MK.Key: {
                        MK.Type: types.String,
                        MK.ContextValidators: (_valid_combination_exists,),
                    },
                    MK.Value: {MK.Type: types.Number},
                },
            },
            "rigs": _rig_schema,
            "slots": _slot_schema,
        },
    }
