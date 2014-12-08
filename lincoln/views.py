import os

from flask import render_template, Blueprint, jsonify, send_from_directory

from . import db, root

main = Blueprint('main', __name__)


@main.route('/')
def home():
    return render_template('home.html')


@main.route('/')
def blocks():
    return render_template('blocks.html')


@main.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(root, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')
