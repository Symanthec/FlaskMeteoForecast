from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from pathlib import Path
from config import Config, basedir

app = Flask(__name__)
app.config.from_object(Config)
app.logger.setLevel(app.config["LOG_LEVEL"])

logger = app.logger

db = SQLAlchemy(app)
from flaskapp import models

if not Path(basedir + "/flaskapp.db").exists():
    logger.warn("Database wasn't found! Creating new")
    db.create_all()

session = db.session

from flaskapp import routes
