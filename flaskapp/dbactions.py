"""
Stores various ways of finding records in DB
Serves for concealing details
"""
from datetime import datetime

from flaskapp.models import Location, User, Weather
from flaskapp.utils import dbdatetime


def location_by_name(city_name: str) -> Location:
    """
    Finds Location in DB by city's name
    :param city_name: Name of the city to find in DB
    :return: Location
    """
    return Location.query.filter_by(name=city_name).first()


def location_by_name_country(city_name: str, country: str) -> Location:
    """
    Finds Location in DB by city's name and country
    :param city_name: Name of the city
    :param country: Country of the city
    :return: Location
    """
    return Location.query.filter_by(name=city_name, country=country).first()


def location_by_coordinates(lat: float, lon: float) -> Location:
    """
    Finds Location in DB by coordinates
    :param lat: latitude
    :param lon: longitude
    :return: Location
    """
    return Location.query.filter_by(latitude=lat, longitude=lon).first()


def user_by_id(user_id: int) -> User:
    """
    Gets User from DB by ID
    Serves only for concealing details
    :param user_id: ID or a primary key of user
    :return: User
    """
    return User.get(user_id)


def user_by_name(name: str) -> User:
    """
    Searches User in DB by name
    :param name: username
    :return: User
    """
    return User.query.filter_by(username=name).first()


def weather_data_by_location_date(location: Location, date_time: datetime):
    """
    Searches for weather records in DB for given Location, date and time
    :param location: Location object of weather
    :param date_time: datetime.datetime of record
    :return: list of Weather objects
    """
    return list(Weather.query.filter_by(location_id=location.location_id, datetime=date_time).all())


def current_weather_by_location(location: Location):
    """
    More specific situation of weather_data_by_location_date for the most relevant records
    :param location: Location object of weather
    :return: list of Weather objects
    """
    return weather_data_by_location_date(location, dbdatetime())
