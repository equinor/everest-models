def rescale_value(value, lower, upper, new_lower, new_upper):
    """Rescale a value with bounds [lower, upper] to the range [new_lower, new_upper]"""
    return (value - lower) * (new_upper - new_lower) / (upper - lower) + new_lower
