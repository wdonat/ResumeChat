
from flask import Flask, render_template, session
from flask_sqlalchemy import SQLAlchemy
from config import config
from flask_login import LoginManager
from flask_cors import CORS, cross_origin

import logging
import threading

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'

def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    app.secret_key = 'twas brillig and the slithy toves'

    CORS(app)
    db.init_app(app)
    login_manager.init_app(app)


    logging.basicConfig(filename='chat_log.txt', format='%(asctime)s %(message)s', level=logging.INFO)

    
    from .api import api as api_blueprint
    app.register_blueprint(api_blueprint, url_prefix='/api/v1')

    return app
