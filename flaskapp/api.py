"""
Gets weather data from:
    - OpenWeatherMap
    - WeatherStack
    - WeatherAPI
    - VisualCrossing
Also adds new locations and weather records to DB
"""
from datetime import datetime
from json import loads
from requests import Response, get
from pycountry import countries

from flaskapp import logger, dbactions, db, app
from flaskapp.models import Location, Weather
from flaskapp.utils import dbdatetime
from flaskapp.weathertypes import WeatherRaw, degrees_to_wind


def kps_to_ms(speed):
    """
    Converts kilometers per second into meters per second
    :param speed: speed expressed in kps
    :return: speed expressed in mps
    """
    return speed / 3.6 if speed is not None else None


def mbar_to_mmhg(pressure):
    """
    Converts millibars to mmhg
    :param pressure: pressure expressed in mbar
    :return: pressure expressed in mmhg
    """
    return pressure * 3 / 4 if pressure is not None else None


class Bundler:
    """
    Class that helps obtaining weather by:
        - Location name
        - Location name and country
        - Coordinates
    """

    @staticmethod
    def current_by_city(city_name, merge: bool = True):
        """
        Gets current weather by location name first from DB, then from from the outside
        :param city_name: Name of location
        :param merge: whether to merge results or not
        :return: list of Weather models and WeatherRaw records
        """
        location = dbactions.location_by_name(city_name)
        results = []
        if location is not None:
            logger.info("location found")
            results = [record.to_raw() for record in dbactions.current_weather_by_location(location)]

        if len(results) == 0:
            date_time = dbdatetime()
            results = [
                # objects declared in the end of file
                owm.get_current_by_city(city_name),
                wapi.get_current_by_city(city_name),
                wstack.get_current_by_city(city_name),
                vcross.get_current_by_city(city_name)
            ]

            location = dbactions.location_by_name(city_name)
            if location is not None:
                for weather in results:
                    if not weather.is_empty():
                        weather = weather.to_model(Weather, date_time, location.location_id)
                        db.session.add(weather)
            db.session.commit()

        if merge:
            return [WeatherRaw.merge(results)], location
        return results, location

    @staticmethod
    def current_by_coordinates(latitude, longitude, merge: bool = True):
        """
        Gets current weather by coordinates first from DB, then from from the outside
        :param latitude: location latitude
        :param longitude: location longitude
        :param merge: whether to merge results or not
        :return: list of WeatherRaw records
        """
        location = dbactions.location_by_coordinates(latitude, longitude)
        results = []
        if location is not None:
            results = [record.to_raw() for record in dbactions.current_weather_by_location(location)]

        if len(results) == 0:
            date_time = dbdatetime()
            results = [
                # objects declared in the end of file
                owm.get_current_by_coordinates(latitude, longitude),
                wapi.get_current_by_coordinates(latitude, longitude),
                wstack.get_current_by_coordinates(latitude, longitude),
                vcross.get_current_by_coordinates(latitude, longitude)
            ]

            location = dbactions.location_by_coordinates(latitude, longitude)
            if location is not None:
                for weather in results:
                    if not weather.is_empty():
                        weather = weather.to_model(Weather, date_time, location.location_id)
                        db.session.add(weather)
            db.session.commit()

        if merge:
            return [WeatherRaw.merge(results)], location
        return results, location

    @staticmethod
    def current_by_city_country(city_name, country, merge: bool = True):
        """
        Gets current weather by city name and country first from DB, then from from the outside
        :param city_name: location name
        :param country: location country
        :param merge: whether to merge results or not
        :return: list of WeatherRaw records
        """
        location = dbactions.location_by_name_country(city_name, country)
        results = []
        if location is not None:
            results = [record.to_raw() for record in dbactions.current_weather_by_location(location)]

        if len(results) == 0:
            date_time = dbdatetime()
            results = [
                # objects declared in the end of file
                owm.get_current_by_city_state_country(city_name, "", country),
                vcross.get_current_by_city_country(city_name, country),
                wstack.get_current_by_city(", ".join([city_name, country])),
            ]

            location = dbactions.location_by_name_country(city_name, country)
            if location is not None:
                for weather in results:
                    if not weather.is_empty():
                        weather = weather.to_model(Weather, date_time, location.location_id)
                        db.session.add(weather)
            db.session.commit()

        if merge:
            return [WeatherRaw.merge(results)], location
        return results, location


class OWM:
    """
    OpenWeatherMap API current weather obtainer
    """
    token = ""
    current_coord_url = "https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={token}"
    current_city_url = "https://api.openweathermap.org/data/2.5/weather?q={city}{state}{country}&appid={token}"

    def __init__(self, token):
        self.set_token(token)

    @staticmethod
    def is_valid_response(response: Response) -> bool:
        """
        Checks whether response is parse-able
        :param response: Response object
        :return: boolean indicating validity of response, error message
        """
        return response.status_code == 200

    def set_token(self, token: str) -> bool:
        """
        Sets token for OpenWeatherMap API
        :param token: string token from OpenWeatherMap API
        :return: whether token is valid or may work
        """
        query = self.current_city_url.format(city="Moscow", state="", country="", token=token)
        if OWM.is_valid_response(get(query)):
            self.token = token
            logger.info("OpenWeatherMap token changed successfully")
            return True
        logger.warn("OpenWeatherMap token remains unchanged")
        return False

    @staticmethod
    def parse_from_response(response: Response) -> WeatherRaw:
        """
        Parses JSON from get_current* requests
        :param response: response containing JSON
        :return: WeatherRaw object
        """
        try:
            json = loads(response.text)
            kwargs = {
                "temperature": json["main"].get("temp", None) - 273.15,
                "humidity": json["main"].get("humidity", None),
                "pressure": mbar_to_mmhg(json["main"].get("pressure", None)),
                "wind_speed": json["wind"].get("speed", None),
                "wind_direction": degrees_to_wind(json["wind"].get("deg", None))
            }

            loc_args = {
                "latitude": json["coord"]["lat"],
                "longitude": json["coord"]["lon"],
                "name": json["name"],
                "country": countries.get(alpha_2=json["sys"]["country"]).name
            }

            location = dbactions.location_by_name(loc_args["name"])
            loc_exists = False
            if location is not None:  # may it be other place?
                loc_exists = dbactions.location_by_coordinates(loc_args["latitude"], loc_args["longitude"]) == location

            if not loc_exists:
                loc_exists = dbactions.location_by_name(loc_args["name"]) is not None
            if not loc_exists:  # for coordinates check, like Kazan and Kazan'
                loc_exists = dbactions.location_by_coordinates(loc_args["latitude"], loc_args["longitude"])

            if not loc_exists:
                location = Location(**loc_args)
                db.session.add(location)
                db.session.commit()

            return WeatherRaw(**kwargs)
        except KeyError:
            logger.error("Error while parsing OWM response:\n", response.text)
            return WeatherRaw.empty()

    def get_current_by_city(self, city_name: str) -> WeatherRaw:
        """
        Gets weather record from past by city name
        :param city_name: name of location
        :return: WeatherRaw
        """
        response = get(self.current_city_url.format(city=city_name, state="", country="", token=self.token))
        if self.is_valid_response(response):
            return self.parse_from_response(response)
        return WeatherRaw.empty()

    def get_current_by_city_state_country(self, city_name: str, state: str, country: str) -> WeatherRaw:
        """
        Gets current weather record by city, state and country
        :param city_name: location's city name
        :param state: location's state name
        :param country: location's country name
        :return: WeatherRaw
        """
        response = get(
            self.current_city_url.format(city=city_name, state="," + state, country="," + country, token=self.token))
        if self.is_valid_response(response):
            return self.parse_from_response(response)
        return WeatherRaw.empty()

    def get_current_by_coordinates(self, latitude, longitude) -> WeatherRaw:
        """
        Gets actual weather record by coordinates and datetime
        :param latitude: latitude of location
        :param longitude: longitude of location
        :return: WeatherRaw
        """
        response = get(self.current_coord_url.format(lat=str(latitude), lon=str(longitude), token=self.token))
        if self.is_valid_response(response):
            return self.parse_from_response(response)
        return WeatherRaw.empty()


class WeatherAPI:
    """
    WeatherAPI current weather obtainer
    """
    token = ""
    cur_city_url = "https://api.weatherapi.com/v1/current.json?key={key}&q={query}&aqi=no"

    def __init__(self, token: str):
        self.set_token(token)

    def set_token(self, token) -> bool:
        """
        Sets token for Weather API
        :param token: string token from Weather API
        :return: whether token is valid or may work
        """
        response = get(self.cur_city_url.format(key=token, query="Moscow"))
        is_good, message = self.is_response_good(response)
        if is_good:
            logger.info("WeatherAPI token changed successfully")
            self.token = token
            return True
        logger.error(f"Error while switching WeatherAPI token: {message}")
        return False

    @staticmethod
    def is_response_good(response: Response):
        """
        Checks whether response is parse-able
        :param response: Response object
        :return: boolean indicating validity of response, error message
        """
        if response.status_code // 100 == 4:
            err_message = loads(response.text)["error"]["message"]
            return False, err_message
        return True, ""

    def get_current_by_city(self, city_name):
        """
        Gets weather record from past by city name
        :param city_name: name of location
        :return: WeatherRaw
        """
        query = self.cur_city_url.format(query=city_name, state="", country="", key=self.token)
        is_good, message = self.is_response_good(get(query))
        if is_good:
            return self.parse_current_weather(get(query))
        logger.error(f"WeatherAPI error: {message}")
        return WeatherRaw.empty()

    def get_current_by_coordinates(self, latitude, longitude):
        """
        Gets actual weather record by coordinates and datetime
        :param latitude: latitude of location
        :param longitude: longitude of location
        :return: WeatherRaw
        """
        query = self.cur_city_url.format(query=str(latitude) + ',' + str(longitude), state="", country="",
                                         key=self.token)
        is_good, message = self.is_response_good(get(query))
        if is_good:
            return self.parse_current_weather(get(query))
        logger.error(f"WeatherAPI error: {message}")
        return WeatherRaw.empty()

    @staticmethod
    def parse_current_weather(response: Response) -> WeatherRaw:
        """
        Parses JSON from get_current* requests
        :param response: response containing JSON
        :return: WeatherRaw object
        """
        try:
            json = loads(response.text)["current"]
            kwargs = {
                "temperature": json.get("temp_c", None),
                "humidity": json.get("humidity", None),
                "pressure": mbar_to_mmhg(json.get("pressure_mb", None)),
                "wind_speed": kps_to_ms(json.get("wind_kph", None)),
                "wind_direction": degrees_to_wind(json.get("wind_degree", None))
            }

            return WeatherRaw(**kwargs)
        except KeyError:
            logger.error("Error while parsing WeatherAPI current weather:\n", response.text)
            return WeatherRaw.empty()


class WeatherStack:
    """
    WeatherStack current weather obtainer
    """
    token = ""
    current_weather_url = "http://api.weatherstack.com/current?access_key={token}&query={query}"

    def __init__(self, token: str):
        self.set_token(token)

    def set_token(self, token):
        """
        Sets token for WeatherStack API
        :param token: string token from WeatherStack
        :return: whether token is valid or may work
        """
        request = self.current_weather_url.format(token=token, query="Moscow")
        is_good, message = self.is_response_good(get(request))
        if is_good:
            logger.info("WeatherStack token changed successfully")
            self.token = token
            return True
        logger.error(f"Error while switching WeatherStack token: {message}")
        return False

    @staticmethod
    def is_response_good(response: Response):
        """
        Checks whether response is parse-able
        :param response: Response object
        :return: boolean indicating validity of response, error message
        """
        if response.status_code != 200:
            json = loads(response.text)
            return False, json["error"]["info"]
        return True, ""

    def get_current_by_city(self, city_name: str) -> WeatherRaw:
        """
        Gets weather record from past by city name
        :param city_name: name of location
        :return: WeatherRaw
        """
        response = get(self.current_weather_url.format(token=self.token, query=city_name))
        is_good, message = self.is_response_good(response)
        if is_good:
            return self.parse_current_weather(response)
        logger.error(f"WeatherStack error while fetching current weather: {message}")
        return WeatherRaw.empty()

    def get_current_by_coordinates(self, latitude: float, longitude: float) -> WeatherRaw:
        """
        Gets actual weather record by coordinates and datetime
        :param latitude: latitude of location
        :param longitude: longitude of location
        :return: WeatherRaw
        """
        response = get(self.current_weather_url.format(token=self.token, query=str(latitude) + "," + str(longitude)))
        is_good, message = self.is_response_good(response)
        if is_good:
            return self.parse_current_weather(response)
        logger.error(f"WeatherStack error while fetching current weather: {message}")
        return WeatherRaw.empty()

    @staticmethod
    def parse_current_weather(response: Response) -> WeatherRaw:
        """
        Parses JSON from get_current* requests
        :param response: response containing JSON
        :return: WeatherRaw object
        """
        try:
            json = loads(response.text)
            kwargs = {
                "temperature": json["current"].get("temperature", None),
                "humidity": json["current"].get("humidity", None),
                "pressure": mbar_to_mmhg(json["current"].get("pressure", None)),
                "wind_speed": kps_to_ms(json["current"].get("wind_speed", None)),
                "wind_direction": degrees_to_wind(json["current"].get("wind_degree", None))
            }

            loc_args = {
                "latitude": json["location"]["lat"],
                "longitude": json["location"]["lon"],
                "name": json["location"]["name"],
                "country": json["location"]["country"]
            }

            location = dbactions.location_by_name(loc_args["name"])
            loc_exists = False
            if location is not None:  # may it be other place?
                loc_exists = dbactions.location_by_coordinates(loc_args["latitude"], loc_args["longitude"]) == location

            if not loc_exists:
                loc_exists = dbactions.location_by_name(loc_args["name"]) is not None
            if not loc_exists:  # for coordinates check, like Kazan and Kazan'
                loc_exists = dbactions.location_by_coordinates(loc_args["latitude"], loc_args["longitude"])

            if not loc_exists:
                location = Location(**loc_args)
                db.session.add(location)
                db.session.commit()

            return WeatherRaw(**kwargs)
        except KeyError:
            logger.error("Error while parsing WeatherStack current weather: \n", response.text)
            return WeatherRaw.empty()


class VisualCrossing:
    """
    Visual Crossing current and historical weather obtainer
    """
    token = ""
    current_weather_url = "https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/" \
                          "{query}?unitGroup=metric&key={token}&include=current"
    history_weather_url = "https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/weatherdata" \
                          "/history?&aggregateHours=24&startDateTime={date}&endDateTime={date}&contentType=json" \
                          "&unitGroup=metric&location={query}&key={token}"

    def __init__(self, token: str):
        self.set_token(token)

    def set_token(self, token):
        """
        Sets token for Visual Crossing API
        :param token: string token from Visual Crossing
        :return: whether token is valid or may work
        """
        request = self.current_weather_url.format(token=token, query="Moscow")
        is_good, message = self.is_response_good(get(request))
        if is_good:
            logger.info("VisualCrossing token changed successfully")
            self.token = token
            return True
        logger.error(f"Error while switching VisualCrossing token: {message}")
        return False

    @staticmethod
    def is_response_good(response: Response):
        """
        Checks whether response is parse-able
        :param response: Response object
        :return: boolean indicating validity of response, error message
        """
        if response.status_code != 200:
            return False, response.text
        return True, ""

    def get_current_by_city(self, city_name: str) -> WeatherRaw:
        """
        Gets weather record from past by city name
        :param city_name: name of location
        :return: WeatherRaw
        """
        response = get(self.current_weather_url.format(token=self.token, query=city_name))
        is_good, message = self.is_response_good(response)
        if is_good:
            return self.parse_current_weather(response)
        logger.error(f"WeatherStack error while fetching current weather: {message}")
        return WeatherRaw.empty()

    def get_current_by_city_country(self, city_name: str, country: str) -> WeatherRaw:
        """
        Gets current weather record by city name and country
        :param city_name: name of location
        :param country: country of location
        :return: WeatherRaw
        """
        response = get(self.current_weather_url.format(token=self.token, query=city_name + "," + country))
        is_good, message = self.is_response_good(response)
        if is_good:
            return self.parse_current_weather(response)
        logger.error(f"WeatherStack error while fetching current weather: {message}")
        return WeatherRaw.empty()

    def get_current_by_coordinates(self, latitude, longitude) -> WeatherRaw:
        """
        Gets actual weather record by coordinates and datetime
        :param latitude: latitude of location
        :param longitude: longitude of location
        :return: WeatherRaw
        """
        response = get(self.current_weather_url.format(token=self.token, query=str(latitude) + ',' + str(longitude)))
        is_good, message = self.is_response_good(response)
        if is_good:
            return self.parse_current_weather(response)
        logger.error(f"WeatherStack error while fetching current weather: {message}")
        return WeatherRaw.empty()

    @staticmethod
    def parse_current_weather(response):
        """
        Parses JSON from get_current* requests
        :param response: response containing JSON
        :return: WeatherRaw object
        """
        try:
            json = loads(response.text)
            kwargs = {
                "temperature": json["currentConditions"].get("temp", None),
                "humidity": json["currentConditions"].get("humidity", None),
                "pressure": mbar_to_mmhg(json["currentConditions"].get("sealevelpressure", None)),
                "wind_speed": kps_to_ms(json["currentConditions"].get("windspeed", None)),
                "wind_direction": degrees_to_wind(json["currentConditions"].get("winddir", None))
            }

            loc_args = {
                "latitude": json["latitude"],
                "longitude": json["longitude"],
                "name": json["address"],
            }

            location = dbactions.location_by_name(loc_args["name"])
            loc_exists = False
            if location is not None:  # may it be other place?
                loc_exists = dbactions.location_by_coordinates(loc_args["latitude"], loc_args["longitude"]) == location

            if not loc_exists:
                loc_exists = dbactions.location_by_name(loc_args["name"]) is not None
            if not loc_exists:  # for coordinates check, like Kazan and Kazan'
                loc_exists = dbactions.location_by_coordinates(loc_args["latitude"], loc_args["longitude"])

            if not loc_exists:
                location = Location(**loc_args)
                db.session.add(location)
                db.session.commit()

            return WeatherRaw(**kwargs)
        except KeyError:
            logger.error("Error while parsing VisualCrossing current weather: \n", response.text)
            return WeatherRaw.empty()

    def get_past_by_city(self, city_name: str, date_time: datetime) -> WeatherRaw:
        """
        Gets weather record from past by city name
        :param city_name: name of location
        :param date_time: date and time of record
        :return: WeatherRaw
        """
        response = get(
            self.history_weather_url.format(date=date_time.strftime("%Y-%m-%dT%H:%M:%S"), token=self.token,
                                            query=city_name))
        is_good, message = self.is_response_good(response)
        if is_good:
            logger.info(response.text)
            return self.parse_past_weather(response)
        logger.error(f"WeatherStack error while fetching current weather: {message}")
        return WeatherRaw.empty()

    def get_past_by_city_country(self, city_name: str, country: str, date_time: datetime) -> WeatherRaw:
        """
        Gets weather record from past by city name and country
        :param city_name: name of location
        :param country: country of location
        :param date_time: date and time of record
        :return: WeatherRaw
        """
        response = get(self.history_weather_url.format(date=date_time.strftime("%Y-%m-%dT%H:%M:%S"), token=self.token,
                                                       query=city_name + "," + country))
        is_good, message = self.is_response_good(response)
        if is_good:
            logger.info("good resp")
            return self.parse_past_weather(response)
        logger.error(f"WeatherStack error while fetching current weather: {message}")
        return WeatherRaw.empty()

    def get_past_by_coordinates(self, latitude, longitude, date_time: datetime) -> WeatherRaw:
        """
        Gets weather record from past by coordinates and datetime
        :param latitude: latitude of location
        :param longitude: longitude of location
        :param date_time: date and time of record
        :return: WeatherRaw
        """
        response = get(self.history_weather_url.format(date=date_time.strftime("%Y-%m-%dT%H:%M:%S"), token=self.token,
                                                       query=str(latitude) + ',' + str(longitude)))
        is_good, message = self.is_response_good(response)
        if is_good:
            return self.parse_past_weather(response)
        logger.error(f"WeatherStack error while fetching current weather: {message}")
        return WeatherRaw.empty()

    @staticmethod
    def parse_past_weather(response: Response) -> WeatherRaw:
        """
        Parses JSON from get_past* requests
        :param response: response containing JSON
        :return: WeatherRaw object
        """
        try:
            json = loads(response.text)["locations"]
            json = json[list(json.keys())[0]]["values"][0]  # get first value in dict -> values
            kwargs = {
                "temperature": json.get("temp", None),
                "pressure": mbar_to_mmhg(json.get("sealevelpressure", None)),
                "humidity": json.get("humidity", None),
                "wind_speed": kps_to_ms(json.get("wspd", None)),
                "wind_direction": degrees_to_wind(json.get("wdir", None))
            }

            loc_args = {
                "latitude": json.get("latitude", None),
                "longitude": json.get("longitude", None),
                "name": json.get("address", None),
            }

            location = dbactions.location_by_name(loc_args["name"])
            loc_exists = False
            if location is not None:  # may it be other place?
                loc_exists = dbactions.location_by_coordinates(loc_args["latitude"], loc_args["longitude"]) == location

            if not loc_exists:
                loc_exists = dbactions.location_by_name(loc_args["name"]) is not None
            if not loc_exists:  # for coordinates check, like Kazan and Kazan'
                loc_exists = dbactions.location_by_coordinates(loc_args["latitude"], loc_args["longitude"])

            if not loc_exists:
                if None not in loc_args.values():
                    location = Location(**loc_args)
                    db.session.add(location)
                    db.session.commit()
                else:
                    print(json)

            return WeatherRaw(**kwargs)
        except KeyError:
            logger.error("Error while parsing VisualCrossing past weather: \n", response.text)
            return WeatherRaw.empty()


owm = OWM(app.config["OWM_TOKEN"])
wapi = WeatherAPI(app.config["WAPI_TOKEN"])
wstack = WeatherStack(app.config["WSTACK_TOKEN"])
vcross = VisualCrossing(app.config["VC_TOKEN"])
