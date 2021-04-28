"""
Various methods, which may be used by many files, but don't classify under one of them
"""
from datetime import datetime


def dbdatetime():
    """
    Application adds new relevant records no sooner than 6 hours from last commit.
    This method gets current time, cuts off minutes, seconds and millis and sets hours multiple to 6
    :return: datetime object with cut off minutes, seconds and millis and hours set multiple to 6
    """
    date_time = datetime.today()
    return date_time.replace(hour=date_time.hour // 6 * 6, minute=0, second=0, microsecond=0)
