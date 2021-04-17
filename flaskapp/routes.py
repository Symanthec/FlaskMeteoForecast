from flask import render_template
from flask import request

from flaskapp import app
from flaskapp.api import OWM, WeatherAPI
from flaskapp.weathertypes import WeatherRaw


@app.route("/")
def index():
    """
        First webpage to be seen by user. May in future show one week forecast based on location.
    """
    return render_template("index.html", title="Home page")


@app.route("/weather")
def weather():
    city = request.args.get("city", None)
    state = request.args.get("state", None)
    country = request.args.get("country", None)

    weatherowm = WeatherRaw.empty()
    weatherapi = WeatherRaw.empty()
    if city is not None:
        if state is not None:
            if country is not None:
                weatherowm = OWM.getCurrentByCityStateCountry(city, state, country)
            else:
                weatherowm = OWM.getCurrentByCityState(city, state)
        else:
            weatherowm = OWM.getCurrentByCity(city)
        weatherapi = WeatherAPI.getCurrentByCity(city)

    return render_template("weather.html", title="Weather forecast", city=city, results=[weatherowm, weatherapi])
