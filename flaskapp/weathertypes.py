from enum import Enum


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
