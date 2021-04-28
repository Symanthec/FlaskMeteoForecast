"""
All ORM models provided by SQLAlchemy declared here
"""
from flaskapp import db
from flaskapp.weathertypes import WindDirection, WeatherRaw
from flaskapp import logger


class User(db.Model):
    """
    User class if for user authentication and preferred weather obtainment
    """
    user_id = db.Column(db.Integer, primary_key=True)
    preferred_location = db.Column(db.Integer)
    username = db.Column(db.String(30), unique=True)
    password_hash = db.Column(db.String(128))

    def __repr__(self):
        return f"<User {self.username}>"


class Location(db.Model):
    """
    Location is responsible for caching and searching for weather records
    """
    location_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    country = db.Column(db.String(100))
    latitude = db.Column(db.Float(precision=.02))
    longitude = db.Column(db.Float)

    def __init__(self, **kwargs):
        super(Location, self).__init__(**kwargs)
        logger.info(f"Location created: {self.name} at {self.latitude};{self.longitude}")

    def __repr__(self):
        return f"<Location {self.name}>"


class Weather(db.Model):
    """
    Weather - bunch of weather parameters for given Location, date and time
    """
    id = db.Column(db.Integer, primary_key=True)
    location_id = db.Column(db.Integer)
    datetime = db.Column(db.DateTime)
    temperature = db.Column(db.Float)
    pressure = db.Column(db.Float)
    humidity = db.Column(db.Float)
    wind_speed = db.Column(db.Float)
    wind_direction = db.Column(db.Enum(WindDirection))

    def to_raw(self) -> WeatherRaw:
        """
        Converts database model into WeatherRaw class for merging and displaying
        :return: WeatherRaw
        """
        return WeatherRaw(temperature=self.temperature,
                          humidity=self.humidity,
                          pressure=self.pressure,
                          wind_speed=self.wind_speed,
                          wind_direction=self.wind_direction)
