import os

from flask import render_template, Blueprint, send_from_directory

import bitcoin.core as core
import bitcoin.base58 as base58

from . import models as m
from . import db, root

main = Blueprint('main', __name__)


@main.route('/address/<address>')
def address(address):
    pubkey_hash = base58.decode(address)
    # Strip off the version and checksum, database doesn't store them
    pubkey_hash = pubkey_hash[1:-4]
    outputs = (m.Output.query.options(db.joinedload('spent_tx'),
                                      db.joinedload('origin_tx')).
               filter_by(dest_address=pubkey_hash))
    return render_template('address.html', outputs=outputs, address=address)


@main.route('/block/<hash>')
def block(hash):
    block = m.Block.query.filter_by(hash=core.lx(hash)).first()
    return render_template('block.html', block=block)


@main.route('/transaction/<hash>')
def transaction(hash):
    transaction = m.Transaction.query.filter_by(txid=core.lx(hash)).first()
    return render_template('transaction.html', transaction=transaction)


@main.route('/transactions')
def transactions():
    transactions = m.Transaction.query.order_by(m.Transaction.id.desc()).limit(100)
    return render_template('transactions.html', transactions=transactions)


@main.route('/')
@main.route('/blocks')
def blocks():
    blocks = m.Block.query.order_by(m.Block.height.desc()).limit(100)
    return render_template('blocks.html', blocks=blocks)


@main.route('/favicon.ico')
def favicon():
    return send_from_directory(
        os.path.join(root, 'static'),
        'favicon.ico', mimetype='image/vnd.microsoft.icon')

@main.route('/search/<query>')
def search(query):
    blob = core.lx(query)
    
    # Query for items
    blocks = m.Block.query.filter(m.Block.hash.like(blob)).limit(10)
    transactions = m.Transaction.query.filter(m.Transaction.txid.like(blob)).limit(10)
    return render_template('search_results.html',
                           blocks=blocks,
                           transactions=transactions)
