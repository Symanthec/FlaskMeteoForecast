from flask import render_template
from flask import request

from flaskapp import app
from flaskapp.api import OWM
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

    weather = WeatherRaw.empty()
    if city is not None:
        if state is not None:
            if country is not None:
                weather = OWM.getCurrentByCityStateCountry(city, state, country)
            else:
                weather = OWM.getCurrentByCityState(city, state)
        else:
            weather = OWM.getCurrentByCity(city)

    return str(weather)
