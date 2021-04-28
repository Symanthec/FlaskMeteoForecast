"""
Flask routes declarations
@app.route("/page")' will stand for making a link on the server to http://ip-address/page
"""
from flask import render_template
from flask import request

from flaskapp import app
from flaskapp.api import Bundler


@app.route("/")
def index():
    """
    Primary page from where user will be able to:
        - Log in to see weather for his preferred locations
        - Fill a form to see current weather or historical records
    """
    return render_template("index.html", title="Home page")


@app.route("/weather")
def weather():
    """
    Displays current weather for cities and given geographical coordinates
    """
    city = request.args.get("city", None)
    country = request.args.get("country", None)
    latitude = request.args.get("lat", None)
    longitude = request.args.get("lon", None)

    results, location = [], {"name": None}
    if city is not None:
        if country is not None:
            results, location = Bundler.current_by_city_country(city, country)
        else:
            results, location = Bundler.current_by_city(city)
    elif latitude is not None and longitude is not None:
        results, location = Bundler.current_by_coordinates(latitude, longitude)

    return render_template("weather.html",
                           title="Weather forecast",
                           location=location,
                           results=results)
