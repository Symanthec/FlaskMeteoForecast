"""
This script refreshes database each 6 hours by removing outdated records
and loading actual weather data for each known location in DB
"""
from datetime import timedelta

from flaskapp import db
from flaskapp.api import Bundler
from flaskapp.models import Weather, Location
from flaskapp.utils import dbdatetime

# deleting outdated by 6 month
edge_date = dbdatetime() + timedelta(-31)
outdated = Weather.query.filter(Weather.datetime <= edge_date).all()
for row in outdated:
    db.session.delete(row)
db.session.commit()

# fetching data for all known Locations
locations = Location.query.all()
print(locations)
for location in locations:
    if location.name is not None:
        if location.country is not None:
            Bundler.current_by_city_country(location.name, location.country)
        else:
            Bundler.current_by_city(location.name)
    elif location.latitude is not None and location.longitude is not None:
        Bundler.current_by_coordinates(location.latitude, location.longitude)