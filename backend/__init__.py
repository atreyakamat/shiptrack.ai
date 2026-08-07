from flask import Flask

from .routes import api


def create_app() -> Flask:
    app = Flask(__name__)
    app.register_blueprint(api, url_prefix="/api/v1")
    return app
