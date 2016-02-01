import os
from uliweb.utils.workers import Worker, Manager
from multiprocessing import Queue
from time import time
from uliweb import functions
from uliweb.orm import Begin, Commit, Rollback, do_, reflect_table, get_connection
import logging

log = logging.getLogger(__name__)

def _warning_check(self):
    return

def patch_mysqldb():
    from uliweb.orm import get_connection

    db = get_connection()
    if db.dialect.driver == 'mysqldb':
        from MySQLdb.cursors import BaseCursor
        setattr(BaseCursor, '_warning_check', _warning_check)

class PutWorker(Worker):
    def __init__(self, filename, queue, max_workers, log=log, *args, **kwargs):
        super(PutWorker, self).__init__(*args, **kwargs)
        self.filename = filename
        self.queue = queue
        self.total = 0
        self.max_workers = max_workers
        self.log = log

    def run(self):
        with open(self.filename) as f:
            f.readline()
            for i, row in enumerate(f):
                self.queue.put(row)
            self.total = i

        for i in range(self.max_workers):
            self.queue.put(None)

        self.is_exit = 'quit'


class InsertWorker(Worker):
    def __init__(self, table, fields, queue, result_queue, log=log, bulk=100,
                 *args, **kwargs):
        super(InsertWorker, self).__init__(*args, **kwargs)
        self.queue = queue
        self.result_queue = result_queue
        self.table = table
        self.fields = fields
        self.total = 0
        self.engine = None
        self.log = log
        self.buf = []
        self.bulk = bulk

    def init(self):
        super(InsertWorker, self).init()
        from uliweb import settings
        from uliweb.orm import Reset, get_session

        patch_mysqldb()
        get_session(create=True)
        # Reset()
        # table = reflect_table(self._table)
        para = dict(zip(self.fields, ['']*len(self.fields)))
        self.sql = str(self.table.insert().values(para))
        # self.sql = self.model.table.insert()
        Begin()

    def run(self):
        import datetime
        from decimal import Decimal

        row = self.queue.get()
        if row == None:
            self.is_exit = 'quit'
            return
        data = eval(row)
        if self.bulk:
            self.buf.append(data)
            if len(self.buf) >= self.bulk:
                do_(self.sql, args=self.buf)
                self.buf = []
        else:
            do_(self.sql, args=[data])
        self.total += 1

    def on_finished(self):
        if self.buf:
            do_(self.sql, args=self.buf)

        Commit()
        self.result_queue.put(self.total)

    def on_exception(self, e):
        Rollback()

def load_table_file(table, filename, max_workers=4, message='', bulk=0, engine=None, delete=True):
    from uliweb.orm import get_connection

    queue = Queue()
    result_queue = Queue()

    engine = engine or get_connection()
    if delete:
        table.drop(engine, checkfirst=True)
        table.create(engine)

    fields = []
    with open(filename) as f:
        line = f.readline()
        fields = line.split()


    workers = []
    workers.append(PutWorker(filename=filename, queue=queue,
                             max_workers=max_workers, name='PutWorker'))
    for i in range(max_workers):
        workers.append(InsertWorker(table=table, fields=fields, queue=queue,
                                    result_queue=result_queue,
                                    name='InsertWorker', bulk=bulk))
    manager = Manager(workers)

    b = time()
    log.info('Starting! {}'.format(message))

    #drop table
    # T = reflect_table(table)
    # engine = get_connection()
    # Model = functions.get_model(table)
    # Model.drop(checkfirst=True)
    # T.drop(engine, checkfirst=True)
    # T.create(engine)
    # Model.table.create()
    manager.start()
    manager.join()
    t = 0
    for i in range(max_workers):
        if not result_queue.empty():
            t += result_queue.get()
        else:
            break

    log.info('Finished! Total {} records, time used: {}'.format(t, time()-b))