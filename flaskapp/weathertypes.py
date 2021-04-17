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
    def merge(*weathers):
        final = {
            "temperature": None,
            "humidity": None,
            "pressure": None,
            "wind_speed": None,
            "wind_direction": []
        }

        final_count = {
            "temperature": 0,
            "humidity": 0,
            "pressure": 0,
            "wind_speed": 0,
        }

        for key in final.keys():
            for weather in weathers:
                if weather[key] is not None:
                    if key == "wind_direction":
                        final[key].append(weather[key])
                        final_count[key] += 1
                    else:
                        if final[key] is None:
                            final[key] = weather[key]
                        else:
                            final[key] += weather[key]
                        final_count[key] += 1

        for key in final.keys()[:-1]:
            if final_count[key] != 0:
                final[key] /= final_count[key]
        final["wind_direction"] = max(final["wind_direction"], key=list.count)

        return WeatherRaw(**final)
