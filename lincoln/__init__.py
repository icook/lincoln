import os
import yaml
import rethinkdb

from bitcoinrpc import AuthServiceProxy
from flask import Flask, g, jsonify, render_template, current_app
from flask.ext.redis import Redis
from flask.ext.rethinkdb import RethinkDB
from werkzeug.local import LocalProxy
from rethinkdb.errors import RqlRuntimeError, RqlDriverError

ROOT = os.path.abspath(os.path.dirname(__file__) + '/../')
RDB_HOST =  os.environ.get('RDB_HOST') or 'localhost'
RDB_PORT = os.environ.get('RDB_PORT') or 28015
db = rethinkdb.db('lincoln')

REDIS_HOST = "localhost"
REDIS_PASSWORD = "password"
REDIS_PORT = 6379
REDIS_DATABASE = 5

r = RethinkDB()
redis = Redis()
coinserv = LocalProxy(
    lambda: getattr(current_app, 'rpc_connection', None))


def create_app():
    app = Flask(__name__)
    app.debug = True
    app.secret_key = 'test'
    app.config.from_object(__name__)
    r.init_app(app)
    redis.init_app(app)

    config_vars = yaml.load(open(ROOT + '/config.yml'))
    # inject all the yaml configs
    app.config.update(config_vars)

    app.rpc_connection = AuthServiceProxy(
        "http://{0}:{1}@{2}:{3}/"
        .format(app.config['coinserv']['username'],
                app.config['coinserv']['password'],
                app.config['coinserv']['address'],
                app.config['coinserv']['port']),
        pool_kwargs=dict(maxsize=10),
        parse_float=float)

    from . import views
    app.register_blueprint(views.main)
    return app
