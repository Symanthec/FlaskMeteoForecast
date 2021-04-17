from json import loads

from requests import Response, get

from flaskapp import logger
from flaskapp.weathertypes import WeatherRaw, degreesToWind


class OWM:
    token = "29e6fcbaa817f82fb78915629169aa0d"
    current_city_url = "https://api.openweathermap.org/data/2.5/weather?q={city}{state}{country}&appid={token}"
    current_id_url = "https://api.openweathermap.org/data/2.5/weather?id={id}&appid={token}"
    current_zip_url = "https://api.openweathermap.org/data/2.5/weather?zip={zip}{country}&appid={token}"

    @staticmethod
    def isValidResponse(response: Response) -> bool:
        if response.status_code != 200:
            return False
        else:
            return True

    @classmethod
    def setToken(cls, token: str) -> bool:
        query = cls.current_city_url.format(city="Moscow", token=token)
        if OWM.isValidResponse(get(query)):
            cls.token = token
            logger.info("Changed token successfully")
            return True
        else:
            logger.warn("Token remains unchanged.")
            return False

    @staticmethod
    def parseFromResponse(response: Response) -> WeatherRaw:
        # try:
        json = loads(response.text)
        wind_degrees = json["wind"]["deg"]
        kwargs = {
            "temperature": json["main"]["temp"] - 273.15,
            "humidity": json["main"]["humidity"],
            "pressure": json["main"]["pressure"] / 4 * 3,
            "wind_speed": json["wind"]["speed"],
            "wind_direction": degreesToWind(wind_degrees)
        }
        # except Exception:
        #     logger.error("OpenWeatherMap: Error occurred while parsing")
        #     return WeatherRaw.empty()
        return WeatherRaw(**kwargs)

    @classmethod
    def getCurrentByCity(cls, cityname: str) -> WeatherRaw:
        response = get(cls.current_city_url.format(city=cityname, state="", country="", token=cls.token))
        if cls.isValidResponse(response):
            return cls.parseFromResponse(response)

    @classmethod
    def getCurrentByCityState(cls, cityname: str, state: str) -> WeatherRaw:
        response = get(cls.current_city_url.format(city=cityname, state="," + state, country="", token=cls.token))
        if cls.isValidResponse(response):
            return cls.parseFromResponse(response)

    @classmethod
    def getCurrentByCityStateCountry(cls, cityname: str, state: str, country: str) -> WeatherRaw:
        response = get(
            cls.current_city_url.format(city=cityname, state="," + state, country="," + country, token=cls.token))
        if cls.isValidResponse(response):
            return cls.parseFromResponse(response)

    @classmethod
    def getCurrentById(cls, cityid: str) -> WeatherRaw:
        response = get(cls.current_id_url.format(id=cityid, token=cls.token))
        if cls.isValidResponse(response):
            return cls.parseFromResponse(response)
