from flask import render_template, flash, url_for
from werkzeug.utils import redirect

from flaskapp import app
from flaskapp.forms.loginform import LoginForm


@app.route("/")
def index():
    return render_template("index.html", title="Home page")


@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        flash(f"Login requested for user {form.username.data}, remember={form.remember.data}")
        return redirect(url_for('login'))
    return render_template("login.html", html_form=form, title="Login page")


@app.route("/register", methods=["GET", "POST"])
def register():
    return "Register page /register"
