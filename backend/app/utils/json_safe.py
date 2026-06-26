import math


def safe_float(value):

    if value is None:
        return None

    if isinstance(value, float):

        if math.isnan(value):
            return None

        if math.isinf(value):
            return None

    return value