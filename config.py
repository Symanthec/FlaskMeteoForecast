import os


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY") or "Hfrux8ahwZk8N8gDJWvK"
