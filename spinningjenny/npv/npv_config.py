from configsuite import types, MetaKeys as MK


def _build_schema():
    return {
        MK.Type: types.NamedDict,
        MK.Content: {
            "prices": {
                MK.Type: types.Dict,
                MK.Description: "Set the prices/values of the production data",
                MK.Content: {
                    MK.Key: {MK.Type: types.String},
                    MK.Value: {
                        MK.Type: types.List,
                        MK.Content: {
                            MK.Item: {
                                MK.Type: types.NamedDict,
                                MK.Content: {
                                    "date": {
                                        MK.Type: types.Date,
                                        MK.Description: "ISO8601 formatted date",
                                    },
                                    "value": {MK.Type: types.Number},
                                    "currency": {
                                        MK.Type: types.String,
                                        MK.Required: False,
                                    },
                                },
                            }
                        },
                    },
                },
            },
            "multiplier": {
                MK.Type: types.Integer,
                MK.Description: "Multiplier to be used.",
                MK.Required: False,
            },
            "files": {
                MK.Type: types.NamedDict,
                MK.Required: False,
                MK.Content: {
                    "input_file": {
                        MK.Type: types.String,
                        MK.Description: (
                            "Path to input file needed in the calculations for well cost. "
                            "The part important for the NPV job is when the well was completed."
                        ),
                        MK.Required: False,
                    },
                    "output_file": {
                        MK.Type: types.String,
                        MK.Description: "Path where to place the outputfile with the npv result.",
                        MK.Required: False,
                    },
                },
            },
            "dates": {
                MK.Type: types.NamedDict,
                MK.Required: False,
                MK.Description: (
                    "Specify the start, end and ref dates for the timeframe of the NPV calculation."
                    "Format dd.mm.yyyy"
                ),
                MK.Content: {
                    "start_date": {
                        MK.Type: types.Date,
                        MK.Description: "ISO8601 formatted date",
                        MK.Required: False,
                    },
                    "end_date": {
                        MK.Type: types.Date,
                        MK.Description: "ISO8601 formatted date",
                        MK.Required: False,
                    },
                    "ref_date": {
                        MK.Type: types.Date,
                        MK.Description: "ISO8601 formatted date",
                        MK.Required: False,
                    },
                },
            },
            "summary_keys": {
                MK.Type: types.List,
                MK.Required: False,
                MK.Description: (
                    "A list of the Eclipse Summary keys to use as part of the NPV calculation."
                    "Defaults to all the vectors with prices supplied."
                ),
                MK.Content: {MK.Item: {MK.Type: types.String}},
            },
            "default_exchange_rate": {
                MK.Type: types.Number,
                MK.Required: False,
                MK.Description: (
                    "Default exchange rate to use if no exchange rate is found at the "
                    "date of a price or cost when currency is specified. "
                ),
            },
            "exchange_rates": {
                MK.Type: types.Dict,
                MK.Required: False,
                MK.Description: (
                    "Set the exchange rates."
                    "All are assumed to be to the NPV currency."
                ),
                MK.Content: {
                    MK.Key: {MK.Type: types.String},
                    MK.Value: {
                        MK.Type: types.List,
                        MK.Content: {
                            MK.Item: {
                                MK.Type: types.NamedDict,
                                MK.Content: {
                                    "date": {
                                        MK.Type: types.Date,
                                        MK.Description: "ISO8601 formatted date",
                                    },
                                    "value": {MK.Type: types.Number},
                                },
                            }
                        },
                    },
                },
            },
            "default_discount_rate": {
                MK.Type: types.Number,
                MK.Required: False,
                MK.Description: (
                    "Default discount rate to use if no discount rate is found at the "
                    "date of a price or cost."
                ),
            },
            "discount_rates": {
                MK.Type: types.List,
                MK.Required: False,
                MK.Description: "Vary the discount rate in time.",
                MK.Content: {
                    MK.Item: {
                        MK.Type: types.NamedDict,
                        MK.Content: {
                            "date": {
                                MK.Type: types.Date,
                                MK.Description: "ISO8601 formatted date",
                            },
                            "value": {MK.Type: types.Number},
                        },
                    }
                },
            },
            "costs": {
                MK.Type: types.List,
                MK.Required: False,
                MK.Description: "Set additional costs to include into the NPV calculation.",
                MK.Content: {
                    MK.Item: {
                        MK.Type: types.NamedDict,
                        MK.Content: {
                            "date": {
                                MK.Type: types.Date,
                                MK.Description: "ISO8601 formatted date",
                            },
                            "value": {MK.Type: types.Number},
                            "currency": {MK.Type: types.String, MK.Required: False},
                        },
                    }
                },
            },
            "well_costs": {
                MK.Type: types.List,
                MK.Required: False,
                MK.Description: (
                    "Set the well costs."
                    "Uses the input file to get date to apply costs at."
                    "Wells not in the input file are not included."
                ),
                MK.Content: {
                    MK.Item: {
                        MK.Type: types.NamedDict,
                        MK.Content: {
                            "well": {MK.Type: types.String},
                            "value": {MK.Type: types.Number},
                            "currency": {MK.Type: types.String, MK.Required: False},
                        },
                    }
                },
            },
        },
    }
