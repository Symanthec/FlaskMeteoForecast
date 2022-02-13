from flaskapp import db
from flaskapp.weathertypes import WindDirection


class User(db.Model):
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), unique=True)
    password_hash = db.Column(db.String(128))
    location = db.relationship("Location", backref='user', lazy="dynamic")

    def __repr__(self):
        return f"<User {self.username}>"


class Location(db.Model):
    location_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    zipcode = db.Column(db.Integer, unique=True)
    cityid = db.Column(db.Integer, unique=True)
    location_user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'))
    states = db.relationship('Weather', backref="location", lazy="dynamic")

    def __repr__(self):
        return f"<Location {self.name}>"


class Weather(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    temperature = db.Column(db.Float)
    pressure = db.Column(db.Float)
    humidity = db.Column(db.Float)
    wind_speed = db.Column(db.Float)
    wind_direction = db.Column(db.Enum(WindDirection))

    def __repr__(self):
        return f"<Weather {self.date}>"
