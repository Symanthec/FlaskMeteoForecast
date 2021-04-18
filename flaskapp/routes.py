from flask import render_template
from flask import request

from flaskapp import app
from flaskapp.api import OWM, WeatherAPI, WeatherStack


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

    weathers = []
    if city is not None:
        if state is not None:
            if country is not None:
                weathers.append(OWM.getCurrentByCityStateCountry(city, state, country))
            else:
                weathers.append(OWM.getCurrentByCityState(city, state))
        else:
            weathers.append(OWM.getCurrentByCity(city))
        weathers.append(WeatherAPI.getCurrentByCity(city))
        weathers.append(WeatherStack.getCurrentByCity(city))

    return render_template("weather.html", title="Weather forecast", city=city, results=weathers)
