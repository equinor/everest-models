# -*- coding: utf-8 -*-

import configsuite
from configsuite import MetaKeys as MK
from configsuite import types


@configsuite.validator_msg("Maximum value must be larger than minimum value")
def _min_max_validation(elem):
    if "max" in elem and "min" in elem:
        return elem["max"] > elem["min"]
    else:
        return True


@configsuite.validator_msg(
    "Only value or min and max should be spesified, value means "
    "this is a constant, min and max means it is a variable"
)
def _value_validation(elem):
    only_min_max = set(elem) == {"min", "max"}
    only_value = set(elem) == {"value"}

    if only_value and only_min_max:
        return False
    if only_value or only_min_max:
        return True
    return False


@configsuite.validator_msg(
    "Only value or options should be spesified, value means "
    "this is a constant, options means it is a variable"
)
def _list_validation(elem):
    if "value" in elem:
        return "options" not in elem or len(elem["options"]) == 0
    return "options" in elem and len(elem["options"]) > 0


def build_schema():
    return {
        MK.Type: types.Dict,
        MK.Description: "Sets the well constraints for indivdual wells",
        MK.Content: {
            MK.Key: {MK.Type: types.String},
            MK.Value: {
                MK.Type: types.Dict,
                MK.Content: {
                    MK.Key: {MK.Type: types.Integer},
                    MK.Value: {
                        MK.Type: types.NamedDict,
                        MK.Content: {
                            "phase": {
                                MK.Description: "Phase must match fluid model",
                                MK.Type: types.NamedDict,
                                MK.ElementValidators: (_list_validation,),
                                MK.Content: {
                                    "value": {
                                        MK.Required: False,
                                        MK.AllowNone: True,
                                        MK.Type: types.String,
                                    },
                                    "options": {
                                        MK.Type: types.List,
                                        MK.Content: {MK.Item: {MK.Type: types.String}},
                                    },
                                },
                            },
                            "rate": {
                                MK.Description: "Rate in reservoir units",
                                MK.Type: types.NamedDict,
                                MK.ElementValidators: (
                                    _min_max_validation,
                                    _value_validation,
                                ),
                                MK.Content: {
                                    "min": {
                                        MK.Required: False,
                                        MK.AllowNone: True,
                                        MK.Type: types.Number,
                                    },
                                    "max": {
                                        MK.Required: False,
                                        MK.AllowNone: True,
                                        MK.Type: types.Number,
                                    },
                                    "value": {
                                        MK.AllowNone: True,
                                        MK.Required: False,
                                        MK.Type: types.Number,
                                    },
                                },
                            },
                            "duration": {
                                MK.Description: "Time in days",
                                MK.Type: types.NamedDict,
                                MK.ElementValidators: (
                                    _min_max_validation,
                                    _value_validation,
                                ),
                                MK.Content: {
                                    "min": {
                                        MK.Required: False,
                                        MK.AllowNone: True,
                                        MK.Type: types.Number,
                                    },
                                    "max": {
                                        MK.Required: False,
                                        MK.AllowNone: True,
                                        MK.Type: types.Number,
                                    },
                                    "value": {
                                        MK.Required: False,
                                        MK.AllowNone: True,
                                        MK.Type: types.Number,
                                    },
                                },
                            },
                        },
                    },
                },
            },
        },
    }
