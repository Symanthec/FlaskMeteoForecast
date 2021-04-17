from json import loads

from requests import Response, get

from flaskapp import logger
from flaskapp.weathertypes import WeatherRaw, degreesToWind


class OWM:
    """ OpenWeatherMap API """
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
        query = cls.current_city_url.format(city="Moscow", state="", country="", token=token)
        if OWM.isValidResponse(get(query)):
            cls.token = token
            logger.info("OpenWeatherMap token changed successfully")
            return True
        else:
            logger.warn("Token remains unchanged.")
            return False

    @staticmethod
    def parseFromResponse(response: Response) -> WeatherRaw:
        json = loads(response.text)
        kwargs = {
            "temperature": json["main"]["temp"] - 273.15,
            "humidity": json["main"]["humidity"],
            "pressure": json["main"]["pressure"] / 4 * 3,
            "wind_speed": json["wind"]["speed"],
            "wind_direction": degreesToWind(json["wind"]["deg"])
        }
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

    @classmethod
    def getCurrentByZip(cls, zipcode: str, country: str) -> WeatherRaw:
        response = get(cls.current_id_url.format(zip=zipcode, country="," + country, token=cls.token))
        if cls.isValidResponse(response):
            return cls.parseFromResponse(response)


class WeatherAPI:
    """ Weather API """
    curcityurl = "https://api.weatherapi.com/v1/current.json?key={key}&q={city}&aqi=no"

    @classmethod
    def setToken(cls, token):
        response = get(cls.curcityurl.format(key=token, city="Moscow"))
        isgood = cls.isResponseGood(response)
        if isgood[0]:
            logger.info("WeatherApi token changed successfully")
            cls.token = token
            return True
        else:
            logger.error(f"Error while switching token: {isgood[1]}")
            return False

    @staticmethod
    def isResponseGood(response):
        if response.status_code // 100 == 4:
            err_message = loads(response.text)["error"]["message"]
            return [False, err_message]
        return [True, ""]

    @classmethod
    def getCurrentByCity(cls, city_name):
        query = cls.curcityurl.format(city=city_name, state="", country="", key=cls.token)
        isgood = cls.isResponseGood(get(query))
        if isgood[0]:
            return cls.parseCurrentWeather(get(query).text)
        else:
            logger.error(f"WeatherAPI error: {isgood[1]}")
            return WeatherRaw.empty()

    @staticmethod
    def parseCurrentWeather(response_text: str) -> WeatherRaw:
        json = loads(response_text)["current"]
        kwargs = {
            "temperature": json["temp_c"],
            "humidity": json["humidity"],
            "pressure": json["pressure_mb"] / 4 * 3,  # из мБар в мм рт ст
            "wind_speed": json["wind_kph"] / 3.6,  # из км/ч в м/с
            "wind_direction": degreesToWind(json["wind_degree"])
        }
        return WeatherRaw(**kwargs)
