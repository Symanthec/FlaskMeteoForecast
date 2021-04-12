import os
import logging

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY") or "Hfrux8ahwZk8N8gDJWvK"

    DATABASE_FILE = 'flaskapp.db'
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL") or 'sqlite:///' + os.path.join(basedir, DATABASE_FILE)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    LOG_LEVEL = os.getenv("LOG_LEVEL") or logging.DEBUG
