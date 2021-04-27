from datetime import datetime
from json import loads
from requests import Response, get
from pycountry import countries

from flaskapp import logger, dbactions, db
from flaskapp.models import Location, Weather
from flaskapp.utils import dbdatetime
from flaskapp.weathertypes import WeatherRaw, degreesToWind


def kps_to_ms(x):
    x / 3.6 if x is not None else None


def mbar_to_mmhg(x):
    return x * 3 / 4 if x is not None else None


class Bundler:

    @staticmethod
    def currentByLocation(location: Location):
        dt = datetime.today()
        dt = dt.replace(hour=dt.hour // 6 * 6, minute=0, second=0, microsecond=0)
        return dbactions.weatherDataByLocationDate(location, dt)

    @staticmethod
    def currentByName(city_name, into_db: bool = True, merge: bool = True):
        dt = dbdatetime()
        results = [
            OWM.getCurrentByCity(city_name),
            WeatherStack.getCurrentByCity(city_name),
            WeatherAPI.getCurrentByCity(city_name),
            VisualCrossing.getCurrentByCity(city_name)
        ]

        if into_db:
            location = dbactions.locationByName(city_name)
            if location is not None:
                for weather in results:
                    in_base = Weather.query.filter_by(temperature=weather.temperature,
                                                      humidity=weather.humidity,
                                                      pressure=weather.pressure,
                                                      wind_speed=weather.wind_speed,
                                                      wind_direction=weather.wind_direction).first() is not None
                    if not (weather.isEmpty() or in_base):
                        weather = weather.toModel(Weather, dt, location.location_id)
                        db.session.add(weather)
            db.session.commit()

        if merge:
            return [WeatherRaw.merge(results)]
        else:
            return results

    @staticmethod
    def currentByCoordinates(lat, lon, into_db: bool = True, merge: bool = True):
        dt = dbdatetime()
        results = [
            OWM.getCurrentByCoordinates(lat, lon),
            WeatherStack.getCurrentByCoordinates(lat, lon),
            WeatherAPI.getCurrentByCoordinates(lat, lon),
            VisualCrossing.getCurrentByCoordinates(lat, lon)
        ]

        if into_db:
            location = dbactions.locationByCoordinates(lat, lon)
            if location is not None:
                for weather in results:
                    in_base = Weather.query.filter_by(temperature=weather.temperature,
                                                      humidity=weather.humidity,
                                                      pressure=weather.pressure,
                                                      wind_speed=weather.wind_speed,
                                                      wind_direction=weather.wind_direction).first() is not None
                    if not (weather.isEmpty() or in_base):
                        weather = weather.toModel(Weather, dt, location.location_id)
                        db.session.add(weather)
            db.session.commit()

        if merge:
            return [WeatherRaw.merge(results)]
        else:
            return results

    @staticmethod
    def currentByCityCountry(name, country, into_db: bool = True, merge: bool = True):
        dt = dbdatetime()
        results = [
            OWM.getCurrentByCityStateCountry(name, "", country),
            VisualCrossing.getCurrentByCityCountry(name, country),
            WeatherStack.getCurrentByCity(", ".join([name, country])),
            WeatherStack.getCurrentByCity(name)
        ]

        if into_db:
            location = dbactions.locationByNameCountry(name, country)
            if location is not None:
                for weather in results:
                    in_base = Weather.query.filter_by(temperature=weather.temperature,
                                                      humidity=weather.humidity,
                                                      pressure=weather.pressure,
                                                      wind_speed=weather.wind_speed,
                                                      wind_direction=weather.wind_direction).first() is not None
                    if not (weather.isEmpty() or in_base):
                        weather = weather.toModel(Weather, dt, location.location_id)
                        db.session.add(weather)
            db.session.commit()

        if merge:
            return [WeatherRaw.merge(results)]
        else:
            return results


class OWM:
    """ OpenWeatherMap API """
    token = ""
    current_coord_url = "https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={token}"
    current_city_url = "https://api.openweathermap.org/data/2.5/weather?q={city}{state}{country}&appid={token}"

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

        loc_args = {
            "latitude": json["coord"]["lat"],
            "longitude": json["coord"]["lon"],
            "name": json["name"],
            "country": countries.get(alpha_2=json["sys"]["country"]).name
        }

        loc_exists = dbactions.locationByNameCountry(loc_args["name"], loc_args["country"]) is not None
        if not loc_exists:
            loc_exists = dbactions.locationByName(loc_args["name"]) is not None

        if not loc_exists:
            location = Location(**loc_args)
            db.session.add(location)
            db.session.commit()

        return WeatherRaw(**kwargs)

    @classmethod
    def getCurrentByCity(cls, city_name: str) -> WeatherRaw:
        response = get(cls.current_city_url.format(city=city_name, state="", country="", token=cls.token))
        if cls.isValidResponse(response):
            return cls.parseFromResponse(response)

    @classmethod
    def getCurrentByCityStateCountry(cls, city_name: str, state: str, country: str) -> WeatherRaw:
        response = get(
            cls.current_city_url.format(city=city_name, state="," + state, country="," + country, token=cls.token))
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

    # Querying by city name and longitude + latitude is pretty same

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
        json = loads(response.text)
        kwargs = {
            "temperature": json["current"].get("temperature", None),
            "humidity": json["current"].get("humidity", None),
            "pressure": mbar_to_mmhg(json["current"].get("pressure", None)),
            "wind_speed": kps_to_ms(json["current"].get("wind_speed", None)),
            "wind_direction": degreesToWind(json["current"].get("wind_degree", None))
        }

        loc_args = {
            "latitude": json["location"]["lat"],
            "longitude": json["location"]["lon"],
            "name": json["location"]["name"],
            "country": json["location"]["country"]
        }

        loc_exists = dbactions.locationByNameCountry(loc_args["name"], loc_args["country"]) is not None
        if not loc_exists:
            loc_exists = dbactions.locationByName(loc_args["name"]) is not None

        if not loc_exists:
            location = Location(**loc_args)
            db.session.add(location)
            db.session.commit()

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
        json = loads(response.text)
        kwargs = {
            "temperature": json["currentConditions"].get("temp", None),
            "humidity": json["currentConditions"].get("humidity", None),
            "pressure": mbar_to_mmhg(json["currentConditions"].get("sealevelpressure", None)),
            "wind_speed": kps_to_ms(json["currentConditions"].get("windspeed", None)),
            "wind_direction": degreesToWind(json["currentConditions"].get("winddir", None))
        }

        loc_args = {
            "latitude": json["latitude"],
            "longitude": json["longitude"],
            "name": json["address"],
        }

        loc_exists = dbactions.locationByName(loc_args["name"]) is not None
        if not loc_exists:
            location = Location(**loc_args)
            db.session.add(location)
            db.session.commit()

        return WeatherRaw(**kwargs)

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
