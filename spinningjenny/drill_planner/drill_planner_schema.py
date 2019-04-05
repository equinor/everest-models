import collections
import configsuite
from configsuite import MetaKeys as MK
from configsuite import types


@configsuite.validator_msg("Should be a defined well")
def _is_well(elem, context):
    return elem in context.wells


@configsuite.validator_msg("Should be a defined slot")
def _is_slot(elem, context):
    return elem in context.slots


@configsuite.validator_msg("Should be prioritized")
def _is_prioritized(elem, context):
    return elem in context.prioritized_wells


@configsuite.validator_msg("Should have drill time")
def _has_drilltime(elem, context):
    return elem in context.scheduled_drill_times


@configsuite.validator_msg("Is x positive")
def _is_positivt(elem):
    return elem > 0


@configsuite.validator_msg("Date should be after defined start date")
def _is_within_time_period(elem, context):
    return context.start_date <= elem <= context.end_date


def extract_validation_context(configuration):
    rigs = tuple([rig.name for rig in configuration.rigs]) if configuration.rigs else ()

    wells = (
        tuple([well.name for well in configuration.wells])
        if configuration.wells
        else ()
    )

    slots = (
        tuple([slot.name for slot in configuration.slots])
        if configuration.slots
        else ()
    )

    prioritized_wells = (
        tuple([well_name for well_name, _ in configuration.wells_priority])
        if configuration.wells_priority
        else ()
    )

    Context = collections.namedtuple(
        "Context",
        ("rigs", "wells", "slots", "start_date", "end_date", "prioritized_wells"),
    )
    return Context(
        rigs,
        wells,
        slots,
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
                            MK.ContextValidators: (_is_well,),
                        }
                    },
                    MK.Description: "List of wells",
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
                    MK.Description: "List of slots",
                },
                "unavailability": {
                    MK.Type: types.List,
                    MK.Required: False,
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
                            MK.ContextValidators: (_is_well,),
                        }
                    },
                    MK.Description: "List of wells",
                },
                "unavailability": {
                    MK.Type: types.List,
                    MK.Required: False,
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
                "name": {MK.Type: types.String, MK.Description: "Well name"},
                "drilltime": {
                    MK.Type: types.Integer,
                    MK.Description: "Drilltime given in days",
                    MK.ElementValidators: (_is_positivt,),
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
                    MK.Key: {MK.Type: types.String, MK.ContextValidators: (_is_well,)},
                    MK.Value: {MK.Type: types.Number},
                },
            },
            "rigs": _rig_schema,
            "slots": _slot_schema,
        },
    }
