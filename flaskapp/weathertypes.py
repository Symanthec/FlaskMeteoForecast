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

    @staticmethod
    def empty():
        return WeatherRaw(temperature=None,
                          humidity=None,
                          pressure=None,
                          wind_speed=None,
                          wind_direction=WindDirection.NONE)

    def isEmpty(self):
        return self.temperature is None and \
               self.humidity is None and \
               self.pressure is None and \
               self.wind_speed is None and \
               self.wind_direction is None

    @staticmethod
    def merge(*weathers):
        final = {
            "temperature": None,
            "humidity": None,
            "pressure": None,
            "wind_speed": None,
            "wind_direction": []
        }

        final_count = [0] * 4
        for weather in weathers:
            has = weather.__dict__
            if "temperature" in has:
                if final["temperature"] is None:
                    final["temperature"] = weather["temperature"]
                final_count[0] += 1
            if "humidity" in has:
                if final["humidity"] is None:
                    final["humidity"] = weather["humidity"]
                final_count[1] += 1
            if "pressure" in has:
                if final["pressure"] is None:
                    final["pressure"] = weather["pressure"]
                final_count[2] += 1
            if "wind_speed" in has:
                if final["wind_speed"] is None:
                    final["wind_speed"] = weather["wind_speed"]
                final_count[3] += 1

            if "wind_direction" in has:
                final["wind_direction"].append(weather["wind_direction"])

        if final_count[0] != 0:
            final["temperature"] /= final_count[0]
        if final_count[1] != 0:
            final["humidity"] /= final_count[1]
        if final_count[2] != 0:
            final["pressure"] /= final_count[2]
        if final_count[3] != 0:
            final["wind_speed"] /= final_count[3]
        final["wind_direction"] = max(final["wind_direction"], key=list.count)

        return WeatherRaw(**final)
