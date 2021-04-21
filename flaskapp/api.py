from datetime import datetime
from json import loads
from requests import Response, get

from flaskapp import logger
from flaskapp.models import WeatherOwm, WeatherWStack, WeatherWapi, WeatherVisual
from flaskapp import db
from flaskapp.weathertypes import WeatherRaw, degreesToWind

kps_to_ms = lambda x: x / 3.6 if x is not None else None
mbar_to_mmhg = lambda x: x * 3 / 4 if x is not None else None


class Bundler:

    @staticmethod
    def bundleByCity(city_name, raw: bool = True, db_add: bool = True):
        owm = OWM.getCurrentByCity(city_name)
        wapi = WeatherAPI.getCurrentByCity(city_name)
        wstack = WeatherStack.getCurrentByCity(city_name)
        visual = VisualCrossing.getCurrentByCity(city_name)

        if db_add:
            if not owm.isEmpty():
                db.session.add(owm.toModel(WeatherOwm))
            if not wapi.isEmpty():
                db.session.add(wapi.toModel(WeatherWapi))
            if not wstack.isEmpty():
                db.session.add(wstack.toModel(WeatherWStack))
            if not visual.isEmpty():
                db.session.add(visual.toModel(WeatherVisual))
            db.session.commit()

        results = [owm, wapi, wstack, visual]

        if raw:
            return results
        else:
            return WeatherRaw.merge(results)

    @staticmethod
    def bundleByCoordinates(latitude, longitude, raw: bool = True, db_add: bool = True):
        owm = OWM.getCurrentByCoordinates(latitude, longitude)
        wapi = WeatherAPI.getCurrentByCoordinates(latitude, longitude)
        wstack = WeatherStack.getCurrentByCoordinates(latitude, longitude)
        visual = VisualCrossing.getCurrentByCoordinates(latitude, longitude)

        if db_add:
            db.session.add(owm.toModel(WeatherOwm))
            db.session.add(wapi.toModel(WeatherWapi))
            db.session.add(wstack.toModel(WeatherWStack))
            db.session.add(visual.toModel(WeatherVisual))
            db.session.commit()

        results = [owm, wapi, wstack, visual]

        if raw:
            return results
        else:
            return WeatherRaw.merge(results)


class OWM:
    """ OpenWeatherMap API """
    token = ""
    current_coord_url = "https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={token}"
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
            "temperature": json["main"].get("temp", None) - 273.15,
            "humidity": json["main"].get("humidity", None),
            "pressure": mbar_to_mmhg(json["main"].get("pressure", None)),
            "wind_speed": json["wind"].get("speed", None),
            "wind_direction": degreesToWind(json["wind"].get("deg", None))
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

    @classmethod
    def getCurrentByCoordinates(cls, lat, lon) -> WeatherRaw:
        response = get(cls.current_coord_url.format(lat=str(lat), lon=str(lon), token=cls.token))
        if cls.isValidResponse(response):
            return cls.parseFromResponse(response)


class WeatherAPI:
    """ Weather API """
    token = ""
    cur_city_url = "https://api.weatherapi.com/v1/current.json?key={key}&q={query}&aqi=no"

    @classmethod
    def setToken(cls, token):
        response = get(cls.cur_city_url.format(key=token, query="Moscow"))
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
        query = cls.cur_city_url.format(query=city_name, state="", country="", key=cls.token)
        is_good, message = cls.isResponseGood(get(query))
        if is_good:
            return cls.parseCurrentWeather(get(query).text)
        else:
            logger.error(f"WeatherAPI error: {message}")
            return WeatherRaw.empty()

    @classmethod
    def getCurrentByCoordinates(cls, lat, lon):
        query = cls.cur_city_url.format(query=str(lat) + ',' + str(lon), state="", country="", key=cls.token)
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
            "temperature": json.get("temp_c", None),
            "humidity": json.get("humidity", None),
            "pressure": mbar_to_mmhg(json.get("pressure_mb", None)),
            "wind_speed": kps_to_ms(json.get("wind_kph", None)),
            "wind_direction": degreesToWind(json.get("wind_degree", None))
        }
        return WeatherRaw(**kwargs)


class WeatherStack:
    token = ""
    current_weather_url = "http://api.weatherstack.com/current?access_key={token}&query={query}"

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
            "temperature": json.get("temperature", None),
            "humidity": json.get("humidity", None),
            "pressure": mbar_to_mmhg(json.get("pressure", None)),
            "wind_speed": kps_to_ms(json.get("wind_speed", None)),
            "wind_direction": degreesToWind(json.get("wind_degree", None))
        }
        return WeatherRaw(**kwargs)


class VisualCrossing:
    token = ""
    current_weather_url = "https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/" \
                          "{query}?unitGroup=metric&key={token}&include=current"
    history_weather_url = "https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/weatherdata" \
                          "/history?&aggregateHours=24&startDateTime={date}&endDateTime={date}&contentType=json" \
                          "&unitGroup=metric&location={query}&key={token}"

    @classmethod
    def setToken(cls, token):
        request = cls.current_weather_url.format(token=token, query="Moscow")
        is_good, message = cls.isResponseGood(get(request))
        if is_good:
            logger.info("VisualCrossing token changed successfully")
            cls.token = token
            return True
        else:
            logger.error(f"Error while switching VisualCrossing token: {message}")
            return False

    @staticmethod
    def isResponseGood(response: Response):
        if response.status_code != 200:
            return False, response.text
        return True, ""

    @classmethod
    def getCurrentByCity(cls, city_name: str) -> WeatherRaw:
        response = get(cls.current_weather_url.format(token=cls.token, query=city_name))
        is_good, message = cls.isResponseGood(response)
        if is_good:
            return cls.parseCurrentWeather(response)
        else:
            logger.error(f"WeatherStack error while fetching current weather: {message}")
            return WeatherRaw.empty()

    @classmethod
    def getCurrentByCityCountry(cls, city_name: str, country: str) -> WeatherRaw:
        response = get(cls.current_weather_url.format(token=cls.token, query=city_name + "," + country))
        is_good, message = cls.isResponseGood(response)
        if is_good:
            return cls.parseCurrentWeather(response)
        else:
            logger.error(f"WeatherStack error while fetching current weather: {message}")
            return WeatherRaw.empty()

    @classmethod
    def getCurrentByCoordinates(cls, latitude, longitude) -> WeatherRaw:
        response = get(cls.current_weather_url.format(token=cls.token, query=str(latitude) + ',' + str(longitude)))
        is_good, message = cls.isResponseGood(response)
        if is_good:
            return cls.parseCurrentWeather(response)
        else:
            logger.error(f"WeatherStack error while fetching current weather: {message}")
            return WeatherRaw.empty()

    @classmethod
    def parseCurrentWeather(cls, response):
        try:
            json = loads(response.text)["currentConditions"]
            kwargs = {
                "temperature": json.get("temp", None),
                "humidity": json.get("humidity", None),
                "pressure": mbar_to_mmhg(json.get("sealevelpressure", None)),
                "wind_speed": kps_to_ms(json.get("windspeed", None)),
                "wind_direction": degreesToWind(json.get("winddir", None))
            }
            return WeatherRaw(**kwargs)
        except KeyError:
            if response.status_code == 200:
                logger.warn("VisualCrossing didn't find current weather records")
            else:
                logger.error(f"VisualCrossing {response.status_code} error: {response.text}")
            return WeatherRaw.empty()

    @classmethod
    def getPastByCity(cls, city_name: str, dt: datetime) -> WeatherRaw:
        response = get(
            cls.history_weather_url.format(date=dt.strftime("%Y-%m-%dT%H:%M:%S"), token=cls.token, query=city_name))
        is_good, message = cls.isResponseGood(response)
        if is_good:
            logger.info(response.text)
            return cls.parsePastWeather(response)
        else:
            logger.error(f"WeatherStack error while fetching current weather: {message}")
            return WeatherRaw.empty()

    @classmethod
    def getPastByCityCountry(cls, city_name: str, country: str, dt: datetime) -> WeatherRaw:
        response = get(cls.history_weather_url.format(date=dt.strftime("%Y-%m-%dT%H:%M:%S"), token=cls.token,
                                                      query=city_name + "," + country))
        is_good, message = cls.isResponseGood(response)
        if is_good:
            logger.info("good resp")
            return cls.parsePastWeather(response)
        else:
            logger.error(f"WeatherStack error while fetching current weather: {message}")
            return WeatherRaw.empty()

    @classmethod
    def getPastByCoordinates(cls, latitude, longitude, dt: datetime) -> WeatherRaw:
        response = get(cls.history_weather_url.format(date=dt.strftime("%Y-%m-%dT%H:%M:%S"), token=cls.token,
                                                      query=str(latitude) + ',' + str(longitude)))
        is_good, message = cls.isResponseGood(response)
        if is_good:
            return cls.parsePastWeather(response)
        else:
            logger.error(f"WeatherStack error while fetching current weather: {message}")
            return WeatherRaw.empty()

    @classmethod
    def parsePastWeather(cls, response: Response) -> WeatherRaw:
        json = loads(response.text)["locations"]
        json = json[list(json.keys())[0]]["values"][0]  # get first value in dict -> values
        kwargs = {
            "temperature": json.get("temp", None),
            "pressure": mbar_to_mmhg(json.get("sealevelpressure", None)),
            "humidity": json.get("humidity", None),
            "wind_speed": kps_to_ms(json.get("wspd", None)),
            "wind_direction": degreesToWind(json.get("wdir", None))
        }

        return WeatherRaw(**kwargs)
