import os
import sys
import yaml
import logging
import inspect

from flask import Flask, current_app
from flask.ext.sqlalchemy import SQLAlchemy
from werkzeug.local import LocalProxy
from bitcoin.rpc import Proxy

import lincoln.filters as filters

root = os.path.abspath(os.path.dirname(__file__) + '/../')
db = SQLAlchemy()

coinserv = LocalProxy(
    lambda: getattr(current_app, 'rpc_connection', None))


def create_app(log_level="INFO", config="config.yml"):
    app = Flask(__name__)
    app.debug = True
    app.secret_key = 'test'
    app.config.from_object(__name__)

    config_vars = yaml.load(open(root + '/config.yml'))
    # inject all the yaml configs
    app.config.update(config_vars)
    db.init_app(app)

    del app.logger.handlers[0]
    app.logger.setLevel(logging.NOTSET)
    log_format = logging.Formatter('%(asctime)s [%(name)s] [%(levelname)s]: %(message)s')
    log_level = getattr(logging, str(log_level), app.config.get('log_level', "INFO"))

    logger = logging.getLogger()
    logger.setLevel(log_level)
    handler = logging.StreamHandler(stream=sys.stdout)
    handler.setFormatter(log_format)
    logger.addHandler(handler)

    # Dynamically add all the filters in the filters.py file
    for name, func in inspect.getmembers(filters, inspect.isfunction):
        app.jinja_env.filters[name] = func

    app.rpc_connection = Proxy(
        "http://{0}:{1}@{2}:{3}/"
        .format(app.config['coinserv']['username'],
                app.config['coinserv']['password'],
                app.config['coinserv']['address'],
                app.config['coinserv']['port'])
        )

    from . import views
    app.register_blueprint(views.main)
    return app
