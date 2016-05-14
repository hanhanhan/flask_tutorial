from flask import Flask
from flask_bootstrap import Bootstrap
from flask_mail import Mail
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy

#how is this found if it's up one folder per tutorial?
#if I'm in the terminal it wouldn't work
from config import config

bootstrap = Bootstrap()
mail = Mail()
moment = Moment()
db = SQLAlchemy()

def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    bootstrap.init_app(app)
    mail.init_app(app)
    moment.init_app(app)
    db.init_app(app)

    #attach routes and custom error pages here
    #view/errors need to import main - imported at bottom to avoid circ dependencies
    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    return app