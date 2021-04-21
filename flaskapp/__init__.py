import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import Config, basedir

# Инициализация Flask

app = Flask(__name__)
app.config.from_object(Config)
app.logger.setLevel(app.config["LOG_LEVEL"])
logger = app.logger

# Инициализация SQLAlchemy
db = SQLAlchemy(app)
from flaskapp import models

database_path = os.path.join(basedir, app.config['DATABASE_FILE'])
if not os.path.exists(database_path):
    logger.warn("Database wasn't found! Creating new")
    db.create_all()

# Инициализация API
from flaskapp.api import OWM, WeatherAPI, WeatherStack, VisualCrossing

OWM.setToken(app.config["OPEN_WEATHER_MAP_TOKEN"])
WeatherAPI.setToken(app.config["WEATHER_API_TOKEN"])
WeatherStack.setToken(app.config["WEATHER_STACK_TOKEN"])
VisualCrossing.setToken(app.config["VISUAL_CROSSING_TOKEN"])


# Путей
from flaskapp import routes
