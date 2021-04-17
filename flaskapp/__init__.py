import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import Config, basedir

app = Flask(__name__)
app.config.from_object(Config)
app.logger.setLevel(app.config["LOG_LEVEL"])

logger = app.logger

db = SQLAlchemy(app)

from flaskapp import models
database_path = os.path.join(basedir, app.config['DATABASE_FILE'])
if not os.path.exists(database_path):
    logger.warn("Database wasn't found! Creating new")
    db.create_all()

from flaskapp.api import OWM, WeatherAPI
OWM.setToken(app.config["OWM_TOKEN"])
WeatherAPI.setToken(app.config["WAPI_TOKEN"])

from flaskapp import routes
