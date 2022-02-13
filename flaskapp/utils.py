from flaskapp import logger


# check if value is of type req_type, else returns default and warns about it.
def check_type(value: object, req_type: type, default: object = None, warn: bool = False) -> object:
    if type(value) != req_type:
        if warn:
            logger.warn(f"Given argument not of a type {type.__name__}. Returning {default}")
        return default
    else:
        return value
