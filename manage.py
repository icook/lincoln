from flask.ext.script import Manager

from lincoln import create_app, r, redis, db, coinserv
import rethinkdb
app = create_app()

manager = Manager(app)

@manager.command
def init_db():
    try:
        rethinkdb.db_create('lincoln').run(r.conn)
        db.table_create('blocks', primary_key='hash').run(r.conn)
        db.table_create('transactions', primary_key='txid').run(r.conn)
        db.table_create('address', primary_key='pubkey').run(r.conn)
        db.table('blocks').index_create('height').run(r.conn)
        db.table('transactions').index_create('time').run(r.conn)
    except rethinkdb.RqlRuntimeError:
        print 'App database already exists.'

@manager.command
def reset_db():
    try:
        rethinkdb.db_drop('lincoln').run(r.conn)
    except rethinkdb.RqlRuntimeError:
        print 'Table doesn\'t exist anyway'

    init_db()

@manager.command
def reset_cache():
    redis.flushdb()

if __name__ == "__main__":
    manager.run()
