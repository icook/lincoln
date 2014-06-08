import gevent
import rethinkdb

from gevent.queue import Queue
from gevent.monkey import patch_all
patch_all()
from decimal import Decimal

from lincoln import create_app, r, redis, db, coinserv


unproced_blocks = Queue()
unproced_block_txs = Queue()


def sync_block():
    print "starting new sync_block"
    with app.app_context():
        while not unproced_blocks.empty():
            hsh = unproced_blocks.get()
            block = coinserv.getblock(hsh)
            if 'nextblockhash' in block:
                unproced_blocks.put(block['nextblockhash'])
            unproced_block_txs.put(block)
            block['txproc'] = False
            res = db.table('blocks').insert(block).run(r.conn)
            if res['errors'] > 0:
                print "Error inserting block {}; hsh: {}".format(block['height'], hsh)
            elif res['inserted'] == 1:
                print "Inserted new block information for block {}; hsh: {}".format(block['height'], hsh)
            else:
                print "Unknown error!"

            if len(block.keys()) != 14:
                print block


def sync_transaction():
    print "starting new sync_transaction"
    with app.app_context():
        while True:
            block = unproced_block_txs.get()
            for tx in block['tx']:
                trans = coinserv.getrawtransaction(tx, 1)
                trans['addrproc'] = False
                res = db.table('transactions').insert(trans).run(r.conn)
                if res['errors'] > 0:
                    print "Error inserting trans for block {}; hsh: {}".format(block['height'], trans['txid'])
                elif res['inserted'] == 1:
                    print "Inserted new trans information for block {}; hsh: {}".format(block['height'], trans['txid'])
                else:
                    print "Unknown error!"

            db.table("blocks").get(block['hash']).update({"txproc": True}).run(r.conn)


def trigger():
    block = list(db.table('blocks').order_by(index=rethinkdb.desc('height')).limit(1).run(r.conn))
    if not block:
        height = 0
    else:
        height = block[0]['height'] + 1

    hsh = coinserv.getblockhash(height)

    print "starting at height {} with hash {}".format(height, hsh)
    unproced_blocks.put(hsh)

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        trigger()
        gevent.joinall([
            gevent.spawn(sync_transaction),
            gevent.spawn(sync_block),
            gevent.spawn(sync_block),
            gevent.spawn(sync_block),
            gevent.spawn(sync_transaction),
        ])
