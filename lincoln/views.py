import os
import datetime

from flask import render_template, Blueprint, send_from_directory, current_app
from decimal import Decimal

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
    results = db.engine.execute(
        "SELECT output.type AS output_type, output.origin_tx_hash AS output_origin_tx_hash, output.amount AS output_amount, output.`index` AS output_index, output.dest_address AS output_dest_address, output.spend_tx_id AS output_spend_tx_id, transaction_1.id AS transaction_1_id, transaction_1.txid AS transaction_1_txid, transaction_1.network_fee AS transaction_1_network_fee, transaction_1.coinbase AS transaction_1_coinbase, transaction_1.block_id AS transaction_1_block_id, transaction_1.total_in AS transaction_1_total_in, transaction_1.total_out AS transaction_1_total_out, transaction_2.id AS transaction_2_id, transaction_2.txid AS transaction_2_txid, transaction_2.network_fee AS transaction_2_network_fee, transaction_2.coinbase AS transaction_2_coinbase, transaction_2.block_id AS transaction_2_block_id, transaction_2.total_in AS transaction_2_total_in, transaction_2.total_out AS transaction_2_total_out FROM output LEFT OUTER JOIN `transaction` AS transaction_1 ON transaction_1.txid = output.origin_tx_hash LEFT OUTER JOIN `transaction` AS transaction_2 ON transaction_2.id = output.spend_tx_id WHERE output.dest_address = :dest_address",
        {"dest_address": pubkey_hash})
    outputs = []
    for row in results:
        output_vals = {k[7:]: v for k, v in row.items() if k.startswith("output_")}
        origin_vals = {k[14:]: v for k, v in row.items() if k.startswith("transaction_1_")}
        spent_vals = {k[14:]: v for k, v in row.items() if k.startswith("transaction_2_")}

        output = m.Output(**output_vals)
        if spent_vals['id'] is not None:
            output.spent_tx = m.Transaction(**spent_vals)
        if origin_vals['id'] is not None:
            output.origin_tx = m.Transaction(**origin_vals)
        outputs.append(output)
    return render_template('address.html', outputs=outputs, address=address)


@main.route('/block/<hash>')
def block(hash):
    block = m.Block.query.filter_by(hash=core.lx(hash)).first()
    current_app.logger.info(m.Block.query.filter_by(hash=core.lx(hash)))
    return render_template('block.html', block=block)


@main.route('/transaction/<hash>')
def transaction(hash):
    results = db.engine.execute(
        "SELECT `transaction`.id AS transaction_id, `transaction`.txid AS transaction_txid, `transaction`.network_fee AS transaction_network_fee, `transaction`.coinbase AS transaction_coinbase, `transaction`.block_id AS transaction_block_id, `transaction`.total_in AS transaction_total_in, `transaction`.total_out AS transaction_total_out, block_1.id AS block_1_id, block_1.hash AS block_1_hash, block_1.height AS block_1_height, block_1.ntime AS block_1_ntime, block_1.orphan AS block_1_orphan, block_1.total_in AS block_1_total_in, block_1.total_out AS block_1_total_out, block_1.difficulty AS block_1_difficulty, block_1.currency AS block_1_currency, block_1.algo AS block_1_algo FROM `transaction` LEFT OUTER JOIN block AS block_1 ON block_1.id = `transaction`.block_id WHERE `transaction`.txid = :txid LIMIT 1",
        {"txid": core.lx(hash)})
    proxy = list(results)[0]
    transaction_vals = {k[12:]: v for k, v in proxy.items() if k.startswith("transaction_")}
    block_vals = {k[8:]: v for k, v in proxy.items() if k.startswith("block_")}
    block_vals['ntime'] = datetime.datetime.utcnow()
    transaction = m.Transaction(**transaction_vals)
    transaction.block = m.Block(**block_vals)

    return render_template('transaction.html', transaction=transaction)


@main.route('/transactions')
def transactions():
    results = db.engine.execute(
        "SELECT `transaction`.id AS transaction_id, `transaction`.txid AS transaction_txid, `transaction`.network_fee AS transaction_network_fee, `transaction`.coinbase AS transaction_coinbase, `transaction`.block_id AS transaction_block_id, `transaction`.total_in AS transaction_total_in, `transaction`.total_out AS transaction_total_out, block_1.id AS block_1_id, block_1.hash AS block_1_hash, block_1.height AS block_1_height, block_1.ntime AS block_1_ntime, block_1.orphan AS block_1_orphan, block_1.total_in AS block_1_total_in, block_1.total_out AS block_1_total_out, block_1.difficulty AS block_1_difficulty, block_1.currency AS block_1_currency, block_1.algo AS block_1_algo FROM `transaction` LEFT OUTER JOIN block AS block_1 ON block_1.id = `transaction`.block_id ORDER BY `transaction`.id DESC LIMIT 100")

    transactions = []
    for row in results:
        block_vals = {k[8:]: v for k, v in row.items() if k.startswith("block_1_")}
        block_vals['ntime'] = datetime.datetime.utcnow()
        transaction_vals = {k[12:]: v for k, v in row.items() if k.startswith("transaction_")}
        transaction_vals['total_in'] = Decimal(transaction_vals['total_in'])
        transaction_vals['total_out'] = Decimal(transaction_vals['total_out'])

        transaction = m.Transaction(**transaction_vals)
        transaction.block = m.Block(**block_vals)
        transactions.append(transaction)
    return render_template('transactions.html', transactions=transactions)


@main.route('/')
@main.route('/blocks')
def blocks():
    blocks = m.Block.query.order_by(m.Block.height.desc()).limit(100)
    current_app.logger.info(blocks)
    return render_template('blocks.html', blocks=blocks)


@main.route('/favicon.ico')
def favicon():
    return send_from_directory(
        os.path.join(root, 'static'),
        'favicon.ico', mimetype='image/vnd.microsoft.icon')
