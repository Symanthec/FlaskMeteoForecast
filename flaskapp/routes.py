from flask import render_template
from flask import request

from flaskapp import app, dbactions, logger
from flaskapp.api import Bundler
from flaskapp.weathertypes import WeatherRaw


@app.route("/")
def index():
    return render_template("index.html", title="Home page")


@app.route("/weather")
def weather():
    city = request.args.get("city", None)
    country_code = request.args.get("country_code", None)
    latitude = request.args.get("lat", None)
    longitude = request.args.get("lon", None)

    results = []

    location = dbactions.locationByName(city)
    if location is None:
        location = dbactions.locationByNameCountry(city, country_code)
    if location is None:
        location = dbactions.locationByCoordinates(latitude, longitude)

    # final query
    if location is not None:
        logger.debug(f"Found {location.name} in database")
        results = dbactions.currentWeatherByLocation(location)
        results = [WeatherRaw.merge([row.toRaw() for row in results])]

    if len(results) == 0:
        if city is not None:
            results = Bundler.currentByName(city, merge=True)
            location = {"name": city}
        elif latitude is not None and longitude is not None:
            results = Bundler.currentByCoordinates(latitude, longitude, merge=True)
            location = {"name": f"Geo-position: {latitude};{longitude}"}

    return render_template("weather.html", title="Weather forecast", location=location, results=results)
