from flask import render_template
from flask import request
from flaskapp import app


@app.route("/")
def index():
    """
        First webpage to be seen by user. May in future show one week forecast based on location.
    """
    return render_template("index.html", title="Home page")
