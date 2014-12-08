import calendar
import datetime
import bitcoin.core as core
import bitcoin.base58 as base58

from flask import current_app

from .model_lib import base
from . import db


class Block(base):
    """ This class stores metadata on all blocks found by the pool """
    # An id value to make foreign keys more compact
    id = db.Column(db.Integer, primary_key=True)
    # the hash of the block
    hash = db.Column(db.LargeBinary(64), unique=True)
    height = db.Column(db.Integer, nullable=False)
    # The actual internal timestamp on the block
    ntime = db.Column(db.DateTime, nullable=False)
    # Is block now orphaned?
    orphan = db.Column(db.Boolean, default=False)
    # Cache of all transactions in and out
    total_in = db.Column(db.Numeric)
    total_out = db.Column(db.Numeric)
    # Difficulty of block when solved
    difficulty = db.Column(db.Float, nullable=False)
    # 3-8 letter code for the currency that was mined
    currency = db.Column(db.String, nullable=False)
    # The hashing algorith mused to solve the block
    algo = db.Column(db.String, nullable=False)

    @property
    def timestamp(self):
        return calendar.timegm(self.ntime.utctimetuple())

    @property
    def url_for(self):
        return "/block/{}".format(self.hash)

    def __str__(self):
        return "<{} h:{} hsh:{}>".format(self.currency, self.height, core.b2lx(self.hash))


class Transaction(base):
    id = db.Column(db.Integer, primary_key=True)
    txid = db.Column(db.LargeBinary(64), unique=True)
    network_fee = db.Column(db.Numeric)
    coinbase = db.Column(db.Boolean)
    # Points to the main chain block that it's in, or null if in mempool
    block_id = db.Column(db.Integer, db.ForeignKey('block.id'))
    block = db.relationship('Block', foreign_keys=[block_id],
                            backref='transactions')
    # Cache of all outputs in and out
    total_in = db.Column(db.Numeric)
    total_out = db.Column(db.Numeric)

    @property
    def url_for(self):
        return "/transaction/{}".format(self.txid)

    @property
    def timestamp(self):
        return calendar.timegm(self.created_at.utctimetuple())

    def __str__(self):
        return "<Transaction h:{}>".format(core.b2lx(self.txid))


class Output(base):
    # Where this Output was created at
    origin_tx_hash = db.Column(db.LargeBinary(64), db.ForeignKey('transaction.txid'), primary_key=True)
    origin_tx = db.relationship('Transaction', foreign_keys=[origin_tx_hash],
                                backref='origin_txs')

    # The amount it's worth
    amount = db.Column(db.Numeric)
    # It's index in the previous tx. Used to query when trying to spend it
    index = db.Column(db.SmallInteger, primary_key=True)

    # Who get's to spend it? Will be null for unusual tx types
    dest_address = db.Column(db.LargeBinary)

    # Point to the tx we spent this output in, or null if UTXO
    spend_tx_id = db.Column(db.Integer, db.ForeignKey('transaction.id'))
    spent_tx = db.relationship('Transaction', foreign_keys=[spend_tx_id],
                               backref='spent_txs')

    @property
    def address_str(self):
        if self.dest_address:
            return base58.CBase58Data.from_bytes(
                self.dest_address,
                nVersion=current_app.config['currency']['address_version'][0])
        else:
            return "Unknown TX Type"

    @property
    def url_for(self):
        return "/transaction/{}".format(self.txid)

    @property
    def timestamp(self):
        return calendar.timegm(self.created_at.utctimetuple())
