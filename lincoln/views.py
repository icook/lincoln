import os

from flask import render_template, Blueprint, jsonify, send_from_directory

import bitcoin.core as core

from . import models as m
from . import db, root

main = Blueprint('main', __name__)


@main.route('/block/<hash>')
def block(hash):
    block = m.Block.query.filter_by(hash=core.lx(hash)).first()
    return render_template('blocks.html', block=block)


@main.route('/')
def blocks():
    blocks = m.Block.query.order_by(m.Block.height.desc()).limit(100)
    return render_template('blocks.html', blocks=blocks)


@main.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(root, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')
