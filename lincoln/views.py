from flask import (current_app, request, render_template, Blueprint, abort, flash,
                   jsonify, g, session, Response)

import rethinkdb
import json

from . import r, redis, db

main = Blueprint('main', __name__)


@main.route('/api/transaction')
def transactions():
    return jsonify(objects=list(db.table('transaction').order_by(index='height').limit(100).run(r.conn)))


@main.route('/api/block')
def blocks():
    return jsonify(objects=list(db.table('blocks').order_by(index='height').limit(100).run(r.conn)))


@main.route('/api/block/<hsh>')
def block(hsh):
    return jsonify(block=dict(db.table('blocks').get(hsh).run(r.conn)))


@main.route('/', methods=['GET', 'POST'])
def home():
    return render_template('home.html')
