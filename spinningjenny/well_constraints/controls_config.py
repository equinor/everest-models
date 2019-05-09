# -*- coding: utf-8 -*-

import configsuite
from configsuite import MetaKeys as MK
from configsuite import types


@configsuite.transformation_msg("Tries to convert input to an integer")
def _to_int(num):
    return int(num)


def _build_schema():
    return {
        MK.Type: types.Dict,
        MK.Description: "Contains controls for wells",
        MK.Content: {
            MK.Key: {MK.Type: types.String},
            MK.Value: {
                MK.Type: types.Dict,
                MK.Content: {
                    MK.Key: {MK.Type: types.Integer, MK.Transformation: _to_int},
                    MK.Value: {MK.Required: True, MK.Type: types.Number},
                },
            },
        },
    }
