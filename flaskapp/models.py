from flaskapp import db
from flaskapp.weathertypes import WindDirection
from flaskapp import logger


class User(db.Model):
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), unique=True)
    password_hash = db.Column(db.String(128))

    def __repr__(self):
        return f"<User {self.username}>"


class Location(db.Model):
    location_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    zipcode = db.Column(db.Integer, unique=True)
    city_id = db.Column(db.Integer, unique=True)

    def __repr__(self):
        return f"<Location {self.name}>"


class WeatherVisual(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    temperature = db.Column(db.Float)
    pressure = db.Column(db.Float)
    humidity = db.Column(db.Float)
    wind_speed = db.Column(db.Float)
    wind_direction = db.Column(db.Enum(WindDirection))

    def __init__(self, **kwargs):
        super(WeatherVisual, self).__init__(**kwargs)
        logger.info("Created VisualCrossing field.")

    def __repr__(self):
        return f"<VisualCrossing Weather {self.date}>"


class WeatherOwm(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    temperature = db.Column(db.Float)
    pressure = db.Column(db.Float)
    humidity = db.Column(db.Float)
    wind_speed = db.Column(db.Float)
    wind_direction = db.Column(db.Enum(WindDirection))

    def __init__(self, **kwargs):
        super(WeatherOwm, self).__init__(**kwargs)
        logger.info("Created OpenWeatherMap field.")

    def __repr__(self):
        return f"<OWM Weather {self.date}>"


class WeatherWStack(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    temperature = db.Column(db.Float)
    pressure = db.Column(db.Float)
    humidity = db.Column(db.Float)
    wind_speed = db.Column(db.Float)
    wind_direction = db.Column(db.Enum(WindDirection))

    def __init__(self, **kwargs):
        super(WeatherWStack, self).__init__(**kwargs)
        logger.info("Created WeatherStack field.")

    def __repr__(self):
        return f"<WeatherStack Weather {self.date}>"


class WeatherWapi(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    temperature = db.Column(db.Float)
    pressure = db.Column(db.Float)
    humidity = db.Column(db.Float)
    wind_speed = db.Column(db.Float)
    wind_direction = db.Column(db.Enum(WindDirection))

    def __init__(self, **kwargs):
        super(WeatherWapi, self).__init__(**kwargs)
        logger.info("Created WeatherAPI field.")

    def __repr__(self):
        return f"<WeatherAPI Weather {self.date}>"
