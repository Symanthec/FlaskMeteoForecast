"""
Flask application loader.
"""
from flaskapp import app

if __name__ == '__main__':
    app.run(debug=app.config["DEBUG"])
