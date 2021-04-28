"""
Flask application's config class holder
"""
import os
import logging

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    """
    A Flask application's pre-init configuration obtainer
    Should receive most of parameters from environment variables
    """
    SECRET_KEY = os.getenv("SECRET_KEY") or "Hfrux8ahwZk8N8gDJWvK"

    DEBUG = os.getenv("DEBUG") or True

    DATABASE_FILE = 'flaskapp.db'
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL") or \
                              'sqlite:///' + os.path.join(basedir, DATABASE_FILE)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    LOG_LEVEL = os.getenv("LOG_LEVEL") or logging.DEBUG

    OWM_TOKEN = os.getenv("OWM_TOKEN") or "29e6fcbaa817f82fb78915629169aa0d"
    WAPI_TOKEN = os.getenv("WAPI_TOKEN") or "f9c01d91dd6b4f26b2d122127211504"
    WSTACK_TOKEN = os.getenv("WSTACK_TOKEN") or "17960f14de602f76776f8fb0a4a872bf"
    VC_TOKEN = os.getenv("VC_TOKEN") or "Q55THSEVUP653NT6YU3E3ECP6"
