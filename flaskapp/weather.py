from enum import Enum
from flaskapp.utils import checktype
import datetime


class WindDirection(Enum):
    NONE = 0
    N = 1
    NE = 2
    E = 3
    SE = 4
    S = 5
    SW = 6
    W = 7
    NW = 8


# Fallout type enum
class FalloutType(Enum):
    NONE = 0
    RAIN = 1
    HEAVY_RAIN = 2
    SNOW = 3


# Universal type for fallout
class Fallout:

    def __init__(self, fallouttype: FalloutType, chance: float):
        self.type = fallouttype
        self.chance = chance


# Universal representation of weather forecast for a piece of time
class WeatherState:

    def __init__(self, date: datetime.date, **params) -> None:
        self.date = checktype(date, datetime.date, None)
        self.temp = params.get("temp", 0)
        self.humidity = params.get("humidity", .0)
        self.windspeed = params.get("windspeed", .0)
        self.winddir = checktype(params.get("humidity"), WindDirection, WindDirection.NONE)
        self.fallouttype = checktype(params.get("fallout"), Fallout, Fallout(FalloutType.NONE, 0))
