from datetime import datetime

from flaskapp import logger


# check if value is of type req_type, else returns default and warns about it.
def check_type(value: object, req_type: type, default: object = None, warn: bool = False) -> object:
    if type(value) != req_type:
        if warn:
            logger.warn(f"Given argument not of a type {type.__name__}. Returning {default}")
        return default
    else:
        return value


def dbdatetime():
    dt = datetime.today()
    return dt.replace(hour=dt.hour // 6 * 6, minute=0, second=0, microsecond=0)
