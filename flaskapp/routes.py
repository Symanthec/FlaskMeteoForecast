from flask import render_template
from flask import request

from flaskapp import app
from flaskapp.api import Bundler


@app.route("/")
def index():
    return render_template("index.html", title="Home page")


@app.route("/weather")
def weather():
    city = request.args.get("city", None)
    latitude = request.args.get("lat", None)
    longitude = request.args.get("lon", None)

    results, location = [], None
    raw = False
    if city is not None:
        if not raw:
            results = [Bundler.bundleByCity(city, raw=raw)]
        else:
            results = Bundler.bundleByCity(city)

        location = city
    elif latitude is not None and longitude is not None:
        if not raw:
            results = [Bundler.bundleByCoordinates(latitude, longitude, raw=raw)]
        else:
            results = Bundler.bundleByCoordinates(latitude, longitude)

        location = f"geoposition: {latitude};{longitude}"

    return render_template("weather.html", title="Weather forecast", location=location, results=results)
