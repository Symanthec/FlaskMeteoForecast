from flask import Flask
# from flask_migrate import Migrate
# from flask_sqlalchemy import SQLAlchemy

from config import Config

app = Flask(__name__)
app.config.from_object(Config)
app.logger.setLevel(app.config["LOG_LEVEL"])

logger = app.logger

# db = SQLAlchemy(app)
# migrate = Migrate(app, db)

from flaskapp import routes

