from base import BaseStorage, KeyError
import time

import sqlalchemy as sa
from sqlalchemy import types

class Storage(BaseStorage):
    def __init__(self, cache_manager, options):
        BaseStorage.__init__(self, cache_manager, options)

        self.url = options.get('url', 'sqlite:///')
        self.tablename = options.get('table_name', 'session')
        self.auto_create = options.get('auto_create', True)
        self.db, self.meta, self.table = create_table(self.url, self.tablename, self.auto_create)
        
    def get(self, key):
        result = sa.select([self.table.c.data, self.table.c.expiry_time,
                            self.table.c.stored_time], 
                           self.table.c.key==key,
                          for_update=True).execute().fetchone()
        if result:
            if self._is_not_expiry(result['stored_time'], result['expiry_time']):
                value = self._load(result['data'])
                return value
        raise KeyError("Cache key [%s] not found" % key)
    
    def set(self, key, value, expire):

        v = self._dump(value)
        result = sa.select([self.table.c.data, self.table.c.id], 
                           self.table.c.key==key,
                          for_update=True).execute().fetchone()
        now = time.time()
        if result:
            self.table.update(self.table.c.id==result['id']).execute(
                data=v, stored_time=now, expiry_time=expire)
        else:
            self.table.insert().execute(key=key, data=v,
                               stored_time=now, expiry_time=expire)
    
    def delete(self, key):
        self.table.delete(self.table.c.key==key).execute()
        return True
            
    def _is_not_expiry(self, accessed_time, expiry_time):
        return time.time() < accessed_time + expiry_time
    
def create_table(url, tablename, create=False):
    db = sa.create_engine(url, strategy='threadlocal')
    meta = sa.MetaData(db)
    table = sa.Table(tablename, meta,
                     sa.Column('id', types.Integer, primary_key=True),
                     sa.Column('key', types.String(64), nullable=False),
                     sa.Column('stored_time', types.Integer, nullable=False),
                     sa.Column('expiry_time', types.Integer, nullable=False),
                     sa.Column('data', types.PickleType, nullable=False),
                     sa.UniqueConstraint('key')
    )
    if create:
        table.create(checkfirst=True)
    return db, meta, table
    