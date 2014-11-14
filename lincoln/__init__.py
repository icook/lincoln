import os
import yaml

from flask.ext.sqlalchemy import SQLAlchemy
from flask import Flask, current_app
from flask.ext.rethinkdb import RethinkDB
from werkzeug.local import LocalProxy
from bitcoin.rpc import Proxy

ROOT = os.path.abspath(os.path.dirname(__file__) + '/../')
db = SQLAlchemy()

r = RethinkDB()
coinserv = LocalProxy(
    lambda: getattr(current_app, 'rpc_connection', None))


def create_app(log_level="INFO", config="config.yml"):
    app = Flask(__name__)
    app.debug = True
    app.secret_key = 'test'
    app.config.from_object(__name__)
    r.init_app(app)

    config_vars = yaml.load(open(ROOT + '/config.yml'))
    # inject all the yaml configs
    app.config.update(config_vars)
    db.init_app(app)

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
