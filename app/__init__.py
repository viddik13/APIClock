from flask import Flask
from flask.ext.bootstrap import Bootstrap
from flask.ext.mail import Mail
from flask.ext.moment import Moment
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import LoginManager
from config import config

import logging
from logging.handlers import RotatingFileHandler
import sys

bootstrap = Bootstrap()
mail      = Mail()
moment    = Moment()
db        = SQLAlchemy()

login_manager                    = LoginManager()
login_manager.session_protection = 'strong'
login_manager.login_view         = 'auth.login'


def create_app(config_name):
    """ Initialize and configure returned Flask instance """
    # Initialize Flask instance
    app = Flask(__name__)
    # Set config to new instance
    app.config.from_object(config[config_name])

    # Configure logging package from app config
    logging.basicConfig(filename=app.config['LOGGING_PATH'] ,level=app.config['LOGGING_LEVEL'])
    logging.getLogger().addHandler(logging.StreamHandler())

    # Initialize config class if needed
    config[config_name].init_app(app)
    bootstrap.init_app(app)
    mail.init_app(app)
    moment.init_app(app)
    db.init_app(app)
    login_manager.init_app(app)

    # Manage blueprint
    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')

    from .alarm import alarm as alarm_blueprint
    app.register_blueprint(alarm_blueprint, url_prefix='/alarm')

    from .radio import radio as radio_blueprint
    app.register_blueprint(radio_blueprint, url_prefix='/radio')

    return app
