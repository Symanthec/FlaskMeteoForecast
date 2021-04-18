from json import loads
from requests import Response, get

from flaskapp import logger
from flaskapp.weathertypes import WeatherRaw, degreesToWind


class OWM:
    """ OpenWeatherMap API """
    token = ""
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
            logger.warn("OpenWeatherMap token remains unchanged")
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
    def getCurrentByCity(cls, city_name: str) -> WeatherRaw:
        response = get(cls.current_city_url.format(city=city_name, state="", country="", token=cls.token))
        if cls.isValidResponse(response):
            return cls.parseFromResponse(response)

    @classmethod
    def getCurrentByCityState(cls, city_name: str, state: str) -> WeatherRaw:
        response = get(cls.current_city_url.format(city=city_name, state="," + state, country="", token=cls.token))
        if cls.isValidResponse(response):
            return cls.parseFromResponse(response)

    @classmethod
    def getCurrentByCityStateCountry(cls, city_name: str, state: str, country: str) -> WeatherRaw:
        response = get(
            cls.current_city_url.format(city=city_name, state="," + state, country="," + country, token=cls.token))
        if cls.isValidResponse(response):
            return cls.parseFromResponse(response)

    @classmethod
    def getCurrentById(cls, city_id: str) -> WeatherRaw:
        response = get(cls.current_id_url.format(id=city_id, token=cls.token))
        if cls.isValidResponse(response):
            return cls.parseFromResponse(response)

    @classmethod
    def getCurrentByZip(cls, zipcode: str, country: str) -> WeatherRaw:
        response = get(cls.current_id_url.format(zip=zipcode, country="," + country, token=cls.token))
        if cls.isValidResponse(response):
            return cls.parseFromResponse(response)


class WeatherAPI:
    """ Weather API """
    token = ""
    cur_city_url = "https://api.weatherapi.com/v1/current.json?key={key}&q={city}&aqi=no"

    @classmethod
    def setToken(cls, token):
        response = get(cls.cur_city_url.format(key=token, city="Moscow"))
        is_good, message = cls.isResponseGood(response)
        if is_good:
            logger.info("WeatherAPI token changed successfully")
            cls.token = token
            return True
        else:
            logger.error(f"Error while switching WeatherAPI token: {message}")
            return False

    @staticmethod
    def isResponseGood(response):
        if response.status_code // 100 == 4:
            err_message = loads(response.text)["error"]["message"]
            return False, err_message
        return True, ""

    @classmethod
    def getCurrentByCity(cls, city_name):
        query = cls.cur_city_url.format(city=city_name, state="", country="", key=cls.token)
        is_good, message = cls.isResponseGood(get(query))
        if is_good:
            return cls.parseCurrentWeather(get(query).text)
        else:
            logger.error(f"WeatherAPI error: {message}")
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


class WeatherStack:
    token = ""
    current_weather_url = "http://api.weatherstack.com/current?access_key={token}&query={query}"
    history_weather_url = "http://api.weatherstack.com/historical?access_key={token}&query={query}" \
                          "&historical_date={date} "

    @classmethod
    def setToken(cls, token):
        request = cls.current_weather_url.format(token=token, query="Moscow")
        is_good, message = cls.isResponseGood(get(request))
        if is_good:
            logger.info("WeatherStack token changed successfully")
            cls.token = token
            return True
        else:
            logger.error(f"Error while switching WeatherStack token: {message}")
            return False

    @staticmethod
    def isResponseGood(response: Response):
        if response.status_code != 200:
            json = loads(response.text)
            return False, json["error"]["info"]
        return True, ""

    # Querying by IP, City name and longitude + latitude is pretty same

    @classmethod
    def getCurrentByCity(cls, query: str) -> WeatherRaw:
        response = get(cls.current_weather_url.format(token=cls.token, query=query))
        is_good, message = cls.isResponseGood(response)
        if is_good:
            return cls.parseCurrentWeather(response)
        else:
            logger.error(f"WeatherStack error while fetching current weather: {message}")
            return WeatherRaw.empty()

    @classmethod
    def getCurrentByIp(cls, query: str) -> WeatherRaw:
        response = get(cls.current_weather_url.format(token=cls.token, query=query))
        is_good, message = cls.isResponseGood(response)
        if is_good:
            return cls.parseCurrentWeather(response)
        else:
            logger.error(f"WeatherStack error while fetching current weather: {message}")
            return WeatherRaw.empty()

    @classmethod
    def getCurrentByCoordinates(cls, latitude: float, longitude: float) -> WeatherRaw:
        response = get(cls.current_weather_url.format(token=cls.token, query=str(latitude) + "," + str(longitude)))
        is_good, message = cls.isResponseGood(response)
        if is_good:
            return cls.parseCurrentWeather(response)
        else:
            logger.error(f"WeatherStack error while fetching current weather: {message}")
            return WeatherRaw.empty()

    @staticmethod
    def parseCurrentWeather(response: Response) -> WeatherRaw:
        json = loads(response.text)["current"]
        kwargs = {
            "temperature": json["temperature"],
            "humidity": json["humidity"],
            "pressure": json["pressure"] / 4 * 3,
            "wind_speed": json["wind_speed"] / 3.6,
            "wind_direction": degreesToWind(json["wind_degree"])
        }
        return WeatherRaw(**kwargs)
