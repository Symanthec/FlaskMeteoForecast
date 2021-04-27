from datetime import datetime

from flaskapp.models import Location, User, Weather


# Location
from flaskapp.utils import dbdatetime


def locationByName(city_name: str) -> Location:
    return Location.query.filter_by(name=city_name).first()


def locationByNameCountry(city_name: str, country: str) -> Location:
    return Location.query.filter_by(name=city_name, country=country).first()


def locationByCoordinates(lat: float, lon: float) -> Location:
    return Location.query.filter_by(latitude=lat, longitude=lon).first()


# User obtain
def userByID(ID: int) -> User:
    return User.get(ID)


def userByName(name: str) -> User:
    return User.query.filter_by(username=name).first()


# Weather obtain
def weatherDataByLocationDate(location: Location, dt: datetime):
    return list(Weather.query.filter_by(location_id=location.location_id, datetime=dt).all())


def currentWeatherByLocation(location: Location):
    return weatherDataByLocationDate(location, dbdatetime())
