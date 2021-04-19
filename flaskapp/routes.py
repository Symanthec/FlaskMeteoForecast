from flask import render_template
from flask import request

from flaskapp import app
from flaskapp.api import Bundler


@app.route("/")
def index():
    """
        First webpage to be seen by user. May in future show one week forecast based on location.
    """
    return render_template("index.html", title="Home page")


@app.route("/weather")
def weather():
    city = request.args.get("city", None)
    latitude = request.args.get("lat", None)
    longitude = request.args.get("lon", None)

    results, location = [], None
    if city is not None:
        results = Bundler.bundleByCity(city)
        location = city
    elif latitude is not None and longitude is not None:
        results = Bundler.bundleByCoordinates(latitude, longitude)
        location = f"geoposition: {latitude};{longitude}"

    return render_template("weather.html", title="Weather forecast", location=location, results=results)
