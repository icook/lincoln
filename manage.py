from flask import current_app
from flask.ext.script import Manager

from lincoln import create_app, db, coinserv
from lincoln.models import Block, Transaction
from bitcoin.core import lx

manager = Manager(create_app)


@manager.command
def init_db():
    db.session.commit()
    db.drop_all()
    db.create_all()


@manager.command
def sync():
    top_hash = lx(coinserv.getbestblockhash())
    top_block = coinserv.getblock(top_hash)
    curr_hash = top_block.GetHash()
    curr_height = top_block.height
    # Find the last block that we've processed
    while True:
        common_ancestor = Block.query.filter_by(hash=top_hash)
        if common_ancestor:
            break
        current_app.logger.info(
            "Didn't find common ancestor at height {}, hsh {}"
            .format(curr_height, curr_hash))
        curr_height -= 1
        curr_hash = coinserv.getblockhash(curr_height)

    current_app.logger.info(
        "Found common ancestor at {}".format(common_ancestor))


manager.add_option('-c', '--config', default='/config.yml')
manager.add_option('-l', '--log-level',
                   choices=['DEBUG', 'INFO', 'WARN', 'ERROR'], default='INFO')

if __name__ == "__main__":
    manager.run()
