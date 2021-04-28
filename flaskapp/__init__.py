"""
__init__.py initializes every part of application:

    - models.py responsible for SQLAlchemy models
    - routes.py for routing links e.g. / and /weather
    - api.py is where most of weather-obtaining and processing code is located

"""
import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import Config, basedir

# Flask component

app = Flask(__name__)
app.config.from_object(Config)
app.logger.setLevel(app.config["LOG_LEVEL"])
logger = app.logger

# SQLAlchemy for database functionality
db = SQLAlchemy(app)
from flaskapp import models

database_path = os.path.join(basedir, app.config['DATABASE_FILE'])
if not os.path.exists(database_path):
    logger.warn("Database wasn't found! Creating new")
    db.create_all()

# API for obtaining weather
from flaskapp import api

# Routes
from flaskapp import routes
