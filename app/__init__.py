import logging

from flask import Flask

from .config import Config


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    from .routes import bp

    app.register_blueprint(bp)

    if app.config.get("RATE_LIMIT_ENABLED", True):
        from flask_limiter import Limiter
        from flask_limiter.util import get_remote_address

        limiter = Limiter(
            get_remote_address,
            app=app,
            storage_uri="memory://",
        )
        limiter.limit(app.config["RATE_LIMIT_SHORTEN"])(
            app.view_functions["urlshortener.shorten_url"]
        )
        limiter.limit(app.config["RATE_LIMIT_REDIRECT"])(
            app.view_functions["urlshortener.redirect_url"]
        )

    return app
