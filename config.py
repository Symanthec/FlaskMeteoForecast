import os
import logging

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY") or "Hfrux8ahwZk8N8gDJWvK"

    DATABASE_FILE = 'flaskapp.db'
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL") or 'sqlite:///' + os.path.join(basedir, DATABASE_FILE)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    LOG_LEVEL = os.getenv("LOG_LEVEL") or logging.DEBUG

    OPEN_WEATHER_MAP_TOKEN = os.getenv("OPEN_WEATHER_MAP_TOKEN") or "29e6fcbaa817f82fb78915629169aa0d"
    WEATHER_API_TOKEN = os.getenv("WEATHER_API_TOKEN") or "f9c01d91dd6b4f26b2d122127211504"
    WEATHER_STACK_TOKEN = os.getenv("WEATHER_STACK_TOKEN") or "17960f14de602f76776f8fb0a4a872bf"
    VISUAL_CROSSING_TOKEN = os.getenv("VISUAL_CROSSING_TOKEN") or "Q55THSEVUP653NT6YU3E3ECP6"
