from json import loads
from datetime import timedelta, datetime
from requests import get

from flaskapp import app, logger, db
from flaskapp.api import mbar_to_mmhg, kps_to_ms
from flaskapp.models import Location, Weather
from flaskapp.utils import dbdatetime
from flaskapp.weathertypes import degrees_to_wind

locations = Location.query.all()
end = dbdatetime()
start = (end + timedelta(-21)).replace(hour=0)

query = "https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/weatherdata" \
        f"/history?&aggregateHours=6&startDateTime={start.strftime('%Y-%m-%dT%H:%M:%S')}&" \
        f"endDateTime={end.strftime('%Y-%m-%dT%H:%M:%S')}&contentType=json&unitGroup=metric" \
        "&location={query}&key=" + app.config["VC_TOKEN"]

for location in locations:
    logger.info(f"Starting {location.name}")
    url_copy = query
    if location.latitude is not None and location.longitude is not None:
        url_copy = url_copy.format(query=str(location.latitude) + "," + str(location.longitude))
    elif location.name is not None:
        if location.country is not None:
            url_copy = url_copy.format(query=location.name + "," + location.country)
        else:
            url_copy = url_copy.format(query=location.name)

    response = get(url_copy)
    if "error_code" not in response.text:
        json = loads(response.text)
        fields = json["locations"][list(json["locations"].keys())[0]]["values"]
        for field in fields:
            kwargs = {
                "temperature": field.get("temp", None),
                "pressure": mbar_to_mmhg(field.get("sealevelpressure", None)),
                "humidity": field.get("humidity", None),
                "wind_speed": kps_to_ms(field.get("wspd", None)),
                "wind_direction": degrees_to_wind(field.get("wdir", None)),
                "datetime": datetime.fromisoformat(field["datetimeStr"]),
                "location_id": location.location_id
            }

            db.session.add(Weather(**kwargs))
        db.session.commit()
