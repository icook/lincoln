import os

from flask import render_template, Blueprint, jsonify, send_from_directory

from . import db, root

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
 
@main.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(root, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')
