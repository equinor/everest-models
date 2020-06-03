from configsuite import validator_msg, types, MetaKeys as MK
from os import path


@validator_msg("Template file found")
def _file_path_validation(file_path):
    return path.exists(file_path)


def build_schema():
    return {
        MK.Type: types.NamedDict,
        MK.Content: {
            "templates": {
                MK.Type: types.List,
                MK.Description: "List of elements containing a template file path "
                "and a set of keys used to match a well operation",
                MK.Content: {
                    MK.Item: {
                        MK.Type: types.NamedDict,
                        MK.Content: {
                            "file": {
                                MK.Description: "Template file path",
                                MK.Type: types.String,
                                MK.ElementValidators: (_file_path_validation,),
                            },
                            "keys": {
                                MK.Description: "Key value pairs to be matched with entries in the well operation elements",
                                MK.Type: types.Dict,
                                MK.Content: {
                                    MK.Value: {MK.Type: types.String},
                                    MK.Key: {MK.Type: types.String},
                                },
                            },
                        },
                    }
                },
            }
        },
    }
