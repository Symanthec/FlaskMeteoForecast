from enum import Enum
from flaskapp.utils import checktype
import datetime


class WindDirection(Enum):
    NONE = "None"
    N = "N"
    NE = "NE"
    E = "E"
    SE = "SE"
    S = "S"
    SW = "SW"
    W = "W"
    NW = "NW"


class FalloutType(Enum):
    NONE = "None"
    RAIN = "Rain"
    HEAVY_RAIN = "Heavy rain"
    SNOW = "Snow"


# Universal type for fallout
class Fallout:
    type = FalloutType.NONE
    chance = 0

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
