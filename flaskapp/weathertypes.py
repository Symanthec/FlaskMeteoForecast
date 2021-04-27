from datetime import datetime
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

    def __str__(self):
        return self.value


wind_map = [
    WindDirection.N,
    WindDirection.NE,
    WindDirection.E,
    WindDirection.SE,
    WindDirection.S,
    WindDirection.SW,
    WindDirection.W,
    WindDirection.NW,
    WindDirection.N
]


def degreesToWind(degrees: float) -> WindDirection:
    if not degrees:
        return WindDirection.NONE
    region = 45  # degrees
    delta = 22.5
    for i in range(9):
        if region * i - delta <= degrees <= region * i + delta:
            return wind_map[i]


class WeatherRaw:

    def __init__(self, **kwargs):
        self.temperature = kwargs.get("temperature", None)
        self.humidity = kwargs.get("humidity", None)
        self.pressure = kwargs.get("pressure", None)
        self.wind_speed = kwargs.get("wind_speed", None)
        self.wind_direction = kwargs.get("wind_direction", WindDirection.NONE)

    def isEmpty(self):
        return self.temperature is None and \
               self.humidity is None and \
               self.pressure is None and \
               self.wind_speed is None and \
               self.wind_direction is None

    @staticmethod
    def empty():
        return WeatherRaw(temperature=None,
                          humidity=None,
                          pressure=None,
                          wind_speed=None,
                          wind_direction=WindDirection.NONE)

    @staticmethod
    def merge(weathers: list):
        final = {
            "temperature": 0,
            "humidity": 0,
            "pressure": 0,
            "wind_speed": 0,
            "wind_direction": []
        }

        final_count = {
            "temperature": 0,
            "humidity": 0,
            "pressure": 0,
            "wind_speed": 0,
        }

        for weather in weathers:
            if weather.temperature is not None:
                final["temperature"] += weather.temperature
                final_count["temperature"] += 1
            if weather.humidity is not None:
                final["humidity"] += weather.humidity
                final_count["humidity"] += 1
            if weather.pressure is not None:
                final["pressure"] += weather.pressure
                final_count["pressure"] += 1
            if weather.wind_speed is not None:
                final["wind_speed"] += weather.wind_speed
                final_count["wind_speed"] += 1
            final["wind_direction"].append(weather.wind_direction)

        for key in list(final.keys())[:-1]:
            if final_count[key] != 0:
                final[key] /= final_count[key]
            else:
                final[key] = None

        tmp_list = list(final["wind_direction"])
        final["wind_direction"] = max(tmp_list, key=tmp_list.count)

        return WeatherRaw(**final)

    def toModel(self, model_type: type, dt: datetime, loc_id: int):
        args = {
            "temperature": self.temperature,
            "humidity": self.humidity,
            "pressure": self.pressure,
            "wind_speed": self.wind_speed,
            "wind_direction": self.wind_direction,
            "datetime": dt,
            "location_id": loc_id
        }
        return model_type(**args)
