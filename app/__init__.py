import os
from flask import Flask
from flask.ext.bootstrap import Bootstrap
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import LoginManager
from flask.ext.moment import Moment
from flask.ext.migrate import Migrate
from flask.ext.mail import Mail

from config import config

bootstrap = Bootstrap()
moment = Moment()
db = SQLAlchemy()
lm = LoginManager()
#Keeps track of the client IP address and browser agent.
#Will log the user out if it detects a change.
lm.session_protectiom = 'strong'
lm.login_view = 'main.login'
migrate = Migrate()
mail = Mail()


def create_app(config_name):
    """Create an application instance."""
    app = Flask(__name__)
    # import configuration
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    # http://stackoverflow.com/questions/33738467/sqlalchemy-who-needs-sqlalchemy-track-modifications
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # initialize extensions
    bootstrap.init_app(app)
    db.init_app(app)
    lm.init_app(app)
    moment.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)

    # import blueprints
    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    return app
