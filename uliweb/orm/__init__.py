# This module is used for wrapping SqlAlchemy to a simple ORM
# Author: limodou <limodou@gmail.com>


__all__ = ['Field', 'get_connection', 'Model', 'do_',
    'set_debug_query', 'set_auto_create', 'set_auto_set_model', 
    'get_model', 'set_model', 'engine_manager', 
    'set_auto_transaction_in_web', 'set_auto_transaction_in_notweb',
    'set_tablename_converter', 'set_check_max_length', 'set_post_do',
    'rawsql', 'Lazy', 'set_echo', 'Session', 'get_session', 'set_session',
    'CHAR', 'BLOB', 'TEXT', 'DECIMAL', 'Index', 'datetime', 'decimal',
    'Begin', 'Commit', 'Rollback', 'Reset', 'ResetAll', 'CommitAll', 'RollbackAll',
    'PICKLE', 'BIGINT', 'set_pk_type', 'PKTYPE', 'FILE', 'INT', 'SMALLINT', 'DATE',
    'TIME', 'DATETIME', 'FLOAT', 'BOOLEAN', 'UUID', 'BINARY', 'VARBINARY',
    'JSON', 'UUID_B',
    'BlobProperty', 'BooleanProperty', 'DateProperty', 'DateTimeProperty',
    'TimeProperty', 'DecimalProperty', 'FloatProperty', 'SQLStorage',
    'IntegerProperty', 'Property', 'StringProperty', 'CharProperty',
    'TextProperty', 'UnicodeProperty', 'Reference', 'ReferenceProperty',
    'PickleProperty', 'BigIntegerProperty', 'FileProperty', 'JsonProperty',
    'UUIDBinaryProperty', 'UUIDProperty',
    'SelfReference', 'SelfReferenceProperty', 'OneToOne', 'ManyToMany',
    'ReservedWordError', 'BadValueError', 'DuplicatePropertyError', 
    'ModelInstanceError', 'KindError', 'ConfigurationError', 'SaveError',
    'BadPropertyTypeError', 'set_lazy_model_init',
    'begin_sql_monitor', 'close_sql_monitor', 'set_model_config', 'text',
    'get_object', 'get_cached_object',
    'set_server_default', 'set_nullable', 'set_manytomany_index_reverse',
    'NotFound', 'reflect_table', 'reflect_table_data', 'reflect_table_model',
    'get_field_type', 'create_model', 'get_metadata', 'migrate_tables',
    'print_model', 'get_model_property', 'Bulk',
    ]

__auto_create__ = False
__auto_set_model__ = True
__auto_transaction_in_web__ = False
__auto_transaction_in_notweb__ = False
__debug_query__ = None
__default_engine__ = 'default'
__default_encoding__ = 'utf-8'
__zero_float__ = 0.0000005
__models__ = {}
__model_paths__ = {}
__pk_type__ = 'int'
__default_tablename_converter__ = None
__check_max_length__ = False #used to check max_length parameter
__default_post_do__ = None #used to process post_do topic
__nullable__ = False    #not enabled null by default
__server_default__ = False    #not enabled null by default
__manytomany_index_reverse__ = False
__lazy_model_init__ = False  

import sys
import decimal
import threading
import datetime
import copy
import re
import cPickle as pickle
from uliweb.utils import date as _date
from uliweb.utils.common import (flat_list, classonlymethod, simple_value, 
    safe_str, import_attr)
from sqlalchemy import *
from sqlalchemy.sql import select, ColumnElement, text, true, and_, false
from sqlalchemy.pool import NullPool
import sqlalchemy.engine.base as EngineBase
from uliweb.core import dispatch
import threading
import warnings
import inspect
from uliweb.utils.sorteddict import SortedDict
from . import patch

Local = threading.local()
Local.dispatch_send = True
Local.conn = {}
Local.trans = {}
Local.echo = False
Local.echo_func = sys.stdout.write

class Error(Exception):pass
class NotFound(Error):
    def __init__(self, message, model, key):
        self.message = message
        self.model = model
        self.key = key
        
    def __str__(self):
        return "{0}({1}) instance can't be found".format(self.model.__name__, str(self.key))
class ModelNotFound(Error):pass
class ReservedWordError(Error):pass
class ModelInstanceError(Error):pass
class DuplicatePropertyError(Error):
    """Raised when a property is duplicated in a model definition."""
class BadValueError(Error):pass
class BadPropertyTypeError(Error):pass
class KindError(Error):pass
class ConfigurationError(Error):pass
class SaveError(Error):pass

_SELF_REFERENCE = object()
class Lazy(object): pass

class SQLStorage(dict):
    """
    a dictionary that let you do d['a'] as well as d.a
    """
    def __getattr__(self, key): return self[key]
    def __setattr__(self, key, value):
        if self.has_key(key):
            raise SyntaxError('Object exists and cannot be redefined')
        self[key] = value
    def __repr__(self): return '<SQLStorage ' + dict.__repr__(self) + '>'

def set_auto_create(flag):
    global __auto_create__
    __auto_create__ = flag
    
def set_auto_transaction_in_notweb(flag):
    global __auto_transaction_in_notweb__
    __auto_transaction_in_notweb__ = flag

def set_auto_transaction_in_web(flag):
    global __auto_transaction_in_web__
    __auto_transaction_in_web__ = flag

def set_auto_set_model(flag):
    global __auto_set_model__
    __auto_set_model__ = flag

def set_debug_query(flag):
    global __debug_query__
    __debug_query__ = flag
    
def set_check_max_length(flag):
    global __check_max_length__
    __check_max_length__ = flag
    
def set_post_do(func):
    global __default_post_do__
    __default_post_do__ = func
    
def set_nullable(flag):
    global __nullable__
    __nullable__ = flag

def set_server_default(flag):
    global __server_default__
    __server_default__ = flag

def set_manytomany_index_reverse(flag):
    global __manytomany_index_reverse__
    __manytomany_index_reverse__ = flag

def set_encoding(encoding):
    global __default_encoding__
    __default_encoding__ = encoding
    
def set_dispatch_send(flag):
    global Local
    Local.dispatch_send = flag
    
def set_tablename_converter(converter=None):
    global __default_tablename_converter__
    __default_tablename_converter__ = converter
    
def set_lazy_model_init(flag):
    global __lazy_model_init__
    __lazy_model_init__ = flag
    
def get_tablename(tablename):
    global __default_tablename_converter__
    
    c = __default_tablename_converter__
    if not c:
        c = lambda x:x.lower()
    return c(tablename)
    
def get_dispatch_send(default=True):
    global Local
    if not hasattr(Local, 'dispatch_send'):
        Local.dispatch_send = default
    return Local.dispatch_send

def set_echo(flag, time=None, explain=False, caller=True, session=None):
    global Local
    
    Local.echo = flag
    Local.echo_args = {'time':time, 'explain':explain, 'caller':caller, 
        'session':None}
    
def set_pk_type(name):
    global __pk_type__
    
    __pk_type__ = name
    
def PKTYPE():
    if __pk_type__ == 'int':
        return int
    else:
        return BIGINT
    
def PKCLASS():
    if __pk_type__ == 'int':
        return Integer
    else:
        return BigInteger
    
class NamedEngine(object):
    def __init__(self, name, options):
        self.name = name
        
        d = SQLStorage({
            'engine_name':name,
            'connection_args':{},
            'debug_log':None,
            'connection_type':'long',
            'duplication':False,
            })
        strategy = options.pop('strategy', None)
        d.update(options)
        if d.get('debug_log', None) is None:
            d['debug_log'] = __debug_query__
        if d.get('connection_type') == 'short':
            d['connection_args']['poolclass'] = NullPool
        if strategy:
            d['connection_args']['strategy'] = strategy

        self.options = d
        self.engine_instance = None
        self.metadata = MetaData()
        self._models = {}
        self.local = threading.local() #used to save thread vars
        
        self._create()

    def _get_models(self):
        if self.options.duplication:
            return engine_manager[self.options.duplication].models
        else:
            return self._models

    models = property(fget=_get_models)

    def _create(self, new=False):
        c = self.options
        
        db = self.engine_instance
        if not self.engine_instance or new:
            args = c.get('connection_args', {})
            self.engine_instance = create_engine(c.get('connection_string'), **args)
        self.engine_instance.echo = c['debug_log']
        self.engine_instance.metadata = self.metadata
        self.metadata.bind = self.engine_instance
            
        return self.engine_instance
        
    def session(self, create=True):
        """
        Used to created default session
        """
        if hasattr(self.local, 'session'):
            return self.local.session
        else:
            if create:
                s = Session(self.name)
                self.local.session = s
                return s

    def set_session(self, session):
        self.local.session = session

    @property
    def engine(self):
        return self.engine_instance
    
    def print_pool_status(self):
        if self.engine.pool:
            print self.engine.pool.status()
    
class EngineManager(object):
    def __init__(self):
        self.engines = {}
        
    def add(self, name, connection_args):
        self.engines[name] = engine = NamedEngine(name, connection_args)
        return engine
        
    def get(self, name=None):
        name = name or __default_engine__
        
        engine = self.engines.get(name)
        if not engine:
            raise Error('Engine %s is not exists yet' % name)
        return engine
    
    def __getitem__(self, name=None):
        return self.get(name)
    
    def __setitem__(self, name, connection_args):
        return self.add(name, connection_args)
    
    def __contains__(self, name):
        return name in self.engines
    
    def items(self):
        return self.engines.items()
    
engine_manager = EngineManager()

class Session(object):
    """
    used to manage relationship between engine_name and connect
    can also manage transcation
    """
    def __init__(self, engine_name=None, auto_transaction=None,
        auto_close=True, post_commit=None, post_commit_once=None):
        """
        If auto_transaction is True, it'll automatically start transacation
        in web environment, it'll be commit or rollback after the request finished
        and in no-web environment, you should invoke commit or rollback yourself.
        """
        self.engine_name = engine_name or __default_engine__
        self.auto_transaction = auto_transaction
        self.auto_close = auto_close
        self.engine = engine_manager[engine_name]
        self._conn = None
        self._trans = None
        self.local_cache = {}
        self.post_commit = post_commit or []
        self.post_commit_once = post_commit_once or []

    def __str__(self):
        return '<Session engine_name:%s, auto_transaction=%r, auto_close=%r>' % (
            self.engine_name, self.auto_transaction, self.auto_close)

    @property
    def need_transaction(self):
        from uliweb import is_in_web

        global __auto_transaction_in_notweb__, __auto_transaction_in_web__
        
        if self.auto_transaction is not None:
            return self.auto_transaction
        else:
            #distinguish in web or not web environment
            if is_in_web():
                return __auto_transaction_in_web__
            else:
                return __auto_transaction_in_notweb__
            
    @property
    def connection(self):
        if self._conn:
            return self._conn
        else:
            self._conn = self.engine.engine.connect()
            return self._conn
        
    def execute(self, query, *args):
        t = self.need_transaction
        try:
            if t:
                self.begin()
            return self.connection.execute(query, *args)
        except:
            if t:
                self.rollback()
            raise
    
    def set_echo(self, flag, time=None, explain=False, caller=True):
        global set_echo
        
        set_echo(flag, time, explain, caller, self)
        
    def do_(self, query, args=None):
        global do_
        
        return do_(query, self, args)
    
    def begin(self):
        if not self._trans:
            self.connection
            self._trans = self._conn.begin()
        return self._trans
    
    def commit(self):
        if self._trans and self._conn.in_transaction():
            self._trans.commit()
        self._trans = None
        if self.auto_close:
            self._close()

        #add post commit hook
        if self.post_commit:
            if not isinstance(self.post_commit, (list, tuple)):
                self.post_commit = [self.post_commit]
            for c in self.post_commit:
                c()

        #add post commit once hook
        if self.post_commit_once:
            if not isinstance(self.post_commit_once, (list, tuple)):
                post_commit_once = [self.post_commit_once]
            else:
                post_commit_once = self.post_commit_once
            self.post_commit_once = []
            for c in post_commit_once:
                c()

    def in_transaction(self):
        if not self._conn:
            return False
        return self._conn.in_transaction()
    
    def rollback(self):
        if self._trans and self._conn.in_transaction():
            self._trans.rollback()
        self._trans = None
        if self.auto_close:
            self._close()
            
    def _close(self):
        if self._conn:
            self._conn.close()
            self._conn = None
            self.local_cache = {}
            
        if self.engine.options.connection_type == 'short':
            self.engine.engine.dispose()
        
    def close(self):
        self.rollback()
        self._close()
        
    def get_local_cache(self, key, creator=None):
        value = self.local_cache.get(key)
        if value:
            return value
        if callable(creator):
            value = creator()
        else:
            value = creator
        if value:
            self.local_cache[key] = value
        return value
        
def get_connection(connection='', engine_name=None, connection_type='long', **args):
    """
    Creating an NamedEngine or just return existed engine instance

    if '://' include in connection parameter, it'll create new engine object
    otherwise return existed engine isntance
    """
    engine_name = engine_name or __default_engine__
    if '://' in connection:
        d = {
            'connection_string':connection,
            'connection_args':args,
            'connection_type':connection_type,
            }
        
        return engine_manager.add(engine_name, d).engine
    else:
        connection = connection or __default_engine__
        if connection in engine_manager:
            return engine_manager[connection].engine
        else:
            raise Error("Can't find engine %s" % connection)
        
def get_metadata(engine_name=None):
    """
    get metadata according used for alembic
    It'll import all tables
    """
    dispatch.get(None, 'load_models')

    engine = engine_manager[engine_name]
    
    for tablename, m in engine.models.items():
        get_model(tablename, engine_name, signal=False)
        if hasattr(m, '__dynamic__') and getattr(m, '__dynamic__'):
            m.table.__mapping_only__ = True
    return engine.metadata

def get_session(ec=None, create=True):
    """
    ec - engine_name or connection
    """
    
    ec = ec or __default_engine__
    if isinstance(ec, (str, unicode)):
        session = engine_manager[ec].session(create=True)
    elif isinstance(ec, Session):
        session = ec
    else:
        raise Error("Connection %r should be existed engine name or Session object" % ec)
    return session

def set_session(session=None, engine_name='default'):
    if not session:
        session = Session()
    engine_manager[engine_name].set_session(session)
    return session

def Reset(ec=None):
    session = get_session(ec, False)
    if session:
        session.close()
    
def ResetAll():
    for k, v in engine_manager.items():
        session = v.session(create=False)
        if session:
            session.close()
    
@dispatch.bind('post_do', kind=dispatch.LOW)
def default_post_do(sender, query, conn, usetime):
    if __default_post_do__:
        __default_post_do__(sender, query, conn, usetime)
      
re_placeholder = re.compile(r'%\(\w+\)s')
def rawsql(query, ec=None):
    """
    ec could be engine name or engine instance
    """
    if isinstance(query, Result):
        query = query.get_query()

    ec = ec or __default_engine__
    if isinstance(ec, (str, unicode)):
        engine = engine_manager[ec]
        dialect = engine.engine.dialect
    else:
        dialect = ec.dialect
    if isinstance(query, (str, unicode)):
        return query
    #return str(query.compile(compile_kwargs={"literal_binds": True})).replace('\n', '') + ';'
    comp = query.compile(dialect=dialect)
    b = re_placeholder.search(comp.string)
    if b:
        return comp.string % comp.params
    else:
        if dialect.name == 'postgresql':
            return comp.string
        else:
            params = []
            for k in comp.positiontup:
                v = comp.params[k]
                params.append(repr(simple_value(v)))
            line = comp.string.replace('?', '%s') % tuple(params)
            return line.replace('\n', '')
    
def get_engine_name(ec=None):
    """
    Get the name of a engine or session
    """
    ec = ec or __default_engine__
    if isinstance(ec, (str, unicode)):
        return ec
    elif isinstance(ec, Session):
        return ec.engine_name
    else:
        raise Error("Parameter ec should be an engine_name or Session object, but %r found" % ec)

def print_model(model, engine_name=None, skipblank=False):
    from sqlalchemy.schema import CreateTable, CreateIndex

    engine = engine_manager[engine_name].engine
    M = get_model(model)
    t = M.table
    s = []
    s.append("%s;" % str(CreateTable(t).compile(dialect=engine.dialect)).rstrip())
    for x in t.indexes:
        s.append("%s;" % CreateIndex(x))
    sql = '\n'.join(s)
    if skipblank:
        return re.sub('[\t\n]+', '', sql)
    else:
        return sql

def do_(query, ec=None, args=None):
    """
    Execute a query
    """
    from time import time
    from uliweb.utils.common import get_caller

    conn = get_session(ec)
    b = time()
    result = conn.execute(query, *(args or ()))
    t = time() - b
    dispatch.call(ec, 'post_do', query, conn, t)
    
    flag = False
    sql = ''
    if hasattr(Local, 'echo') and Local.echo:
        if hasattr(Local, 'echo_args'):
            _ec = Local.echo_args.get('session')
        else:
            _ec = None
        engine_name = get_engine_name(ec)
        _e = get_engine_name(_ec)
        
        if not _ec or _ec and _ec == _e:
            if hasattr(Local, 'echo_args') and Local.echo_args['time']:
                if t >= Local.echo_args['time']:
                    sql = rawsql(query)
                    
                    flag = True
            else:
                sql = rawsql(query)
                flag = True
        
        if flag:
            print '\n===>>>>> [%s]' % engine_name,
            if hasattr(Local, 'echo_args') and Local.echo_args['caller']:
                v = get_caller(skip=__file__)
                print '(%s:%d:%s)' % v
            else:
                print
            print sql+';'
            if hasattr(Local, 'echo_args') and Local.echo_args['explain'] and sql:
                r = conn.execute('explain '+sql).fetchone()
                print '\n----\nExplain: %s' % ''.join(["%s=%r, " % (k, v) for k, v in r.items()])
            print '===<<<<< time used %fs\n' % t
                
    return result

def save_file(result, filename, encoding='utf8', headers=None,
              convertors=None, visitor=None, **kwargs):
    """
    save query result to a csv file
    visitor can used to convert values, all value should be convert to string
    visitor function should be defined as:
        def visitor(keys, values, encoding):
            #return new values []
    
    convertors is used to convert single column value, for example:
        
        convertors = {'field1':convert_func1, 'fields2':convert_func2}
        
        def convert_func1(value, data):
            value is value of field1
            data is the record
            
    if visitor and convertors all provided, only visitor is available.
    
    headers used to convert column to a provided value
    """
    import csv
    from uliweb.utils.common import simple_value
    
    convertors = convertors or {}
    headers = headers or {}
    
    def convert(k, v, data):
        f = convertors.get(k)
        if f:
            v = f(v, data)
        return v
    
    def convert_header(k):
        return headers.get(k, k)
    
    def _r(x):
        if isinstance(x, (str, unicode)):
            return re.sub('\r\n|\r|\n', ' ', x)
        else:
            return x

    if isinstance(filename, (str, unicode)):
        f = open(filename, 'wb')
        need_close = True
    else:
        f = filename
        need_close = False

    try:
        w = csv.writer(f, **kwargs)
        w.writerow([simple_value(convert_header(x), encoding=encoding) for x in result.keys()])
        for row in result:
            if visitor and callable(visitor):
                _row = visitor(result.keys, row.values(), encoding)
            else:
                _row = [convert(k, v, row) for k, v in zip(result.keys(), row.values())]
            r = [simple_value(_r(x), encoding=encoding) for x in _row]
            w.writerow(r)
    finally:
        if need_close:
            f.close()

    
def Begin(ec=None):
    session = get_session(ec)
    return session.begin()

def Commit(ec=None, close=None):
    if close:
        warnings.simplefilter('default')
        warnings.warn("close parameter will not need at all.", DeprecationWarning)
        
    session = get_session(ec, False)
    if session:
        return session.commit()
    
def CommitAll(close=None):
    """
    Commit all transactions according Local.conn
    """
    if close:
        warnings.simplefilter('default')
        warnings.warn("close parameter will not need at all.", DeprecationWarning)
    
    for k, v in engine_manager.items():
        session = v.session(create=False)
        if session:
            session.commit()
    
def Rollback(ec=None, close=None):
    if close:
        warnings.simplefilter('default')
        warnings.warn("close parameter will not need at all.", DeprecationWarning)

    session = get_session(ec, False)
    if session:
        return session.rollback()
    
def RollbackAll(close=None):
    """
    Rollback all transactions, according Local.conn
    """
    if close:
        warnings.simplefilter('default')
        warnings.warn("close parameter will not need at all.", DeprecationWarning)

    for k, v in engine_manager.items():
        session = v.session(create=False)
        if session:
            session.rollback()
    
def check_reserved_word(f):
    if f in ['put', 'save', 'table', 'tablename', 'c', 'columns', 'manytomany'] or f in dir(Model):
        raise ReservedWordError(
            "Cannot define property using reserved word '%s'. " % f
            )

def set_model(model, tablename=None, created=None, appname=None, model_path=None):
    """
    Register an model and tablename to a global variable.
    model could be a string format, i.e., 'uliweb.contrib.auth.models.User'

    :param appname: if no appname, then archive according to model

    item structure
        created
        model
        model_path
        appname

    For dynamic model you should pass model_path with '' value
    """
    if isinstance(model, type) and issubclass(model, Model):
        #use alias first
        tablename = model._alias or model.tablename
    tablename = tablename.lower()
    #set global __models__
    d = __models__.setdefault(tablename, {})
    engines = d.get('config', {}).pop('engines', ['default'])
    if isinstance(engines, (str, unicode)):
        engines = [engines]
    d['engines'] = engines
    
    item = {}
    if created is not None:
        item['created'] = created
    else:
        item['created'] = None
    if isinstance(model, (str, unicode)):
        if model_path is None:
            model_path = model
        else:
            model_path = model_path
        if not appname:
            appname = model.rsplit('.', 2)[0]
        #for example 'uliweb.contrib.auth.models.User'
        model = None
    else:
        appname = model.__module__.rsplit('.', 1)[0]
        if model_path is None:
            model_path = model.__module__ + '.' + model.__name__
        else:
            model_path = ''
        #for example 'uliweb.contrib.auth.models'
        model.__engines__ = engines
        
    item['model'] = model
    item['model_path'] = model_path
    item['appname'] = appname
    d['model_path'] = model_path
    d['appname'] = appname

    for name in engines:
        if not isinstance(name, (str, unicode)):
            raise BadValueError('Engine name should be string type, but %r found' % name)
    
        engine_manager[name].models[tablename] = item.copy()
    
def set_model_config(model_name, config, replace=False):
    """
    This function should be only used in initialization phrase
    :param model_name: model name it's should be string
    :param config: config should be dict. e.g.
        {'__mapping_only__', '__tablename__', '__ext_model__'}
    :param replace: if True, then replace original config, False will update
    """
    assert isinstance(model_name, str)
    assert isinstance(config, dict)
    
    d = __models__.setdefault(model_name, {})
    if replace:
        d['config'] = config
    else:
        c = d.setdefault('config', {})
        c.update(config)

def create_model(modelname, fields, indexes=None, basemodel=None, **props):
    """
    Create model dynamically

    :param fields: Just format like [
                        {'name':name, 'type':type, ...},
                        ...
                        ]
                    type should be a string, eg. 'str', 'int', etc
                    kwargs will be passed to Property.__init__() according field type,
                    it'll be a dict
    :param props: Model attributes, such as '__mapping_only__', '__replace__'
    :param indexes: Multiple fields index, single index can be set directly using `index=True`
                    to a field, the value format should be:

                    [
                        {'name':name, 'fields':[...], ...},
                    ]

                    e.g. [
                        {'name':'audit_idx', 'fields':['table_id', 'obj_id']}
                    ]

                    for kwargs can be ommited.

    :param basemodel: Will be the new Model base class, so new Model can inherited
                    parent methods, it can be a string or a real class object
    """
    assert not props or isinstance(props, dict)
    assert not indexes or isinstance(indexes, list)

    props = SortedDict(props or {})
    props['__dynamic__'] = True
    props['__config__'] = False

    for p in fields:
        kwargs = p.copy()
        name = kwargs.pop('name')
        _type = kwargs.pop('type')

        #if the key is start with '_', then remove it
        for k in kwargs.keys():
            if k.startswith('_'):
                kwargs.pop(k, None)

        field_type = get_field_type(_type)
        prop = field_type(**kwargs)
        props[name] = prop

    if basemodel:
        model = import_attr(basemodel)
        # model.clear_relation()
    else:
        model = Model
    # try:
    #     old = get_model(modelname, signal=False)
    #     old.clear_relation()
    # except ModelNotFound as e:
    #     pass

    cls = type(str(modelname.title()), (model,), props)

    tablename = props.get('__tablename__', modelname)
    set_model(cls, tablename, appname=__name__, model_path='')
    get_model(modelname, signal=False, reload=True)

    indexes = indexes or []
    for x in indexes:
        kwargs = x.copy()
        name = kwargs.pop('name')
        fields = kwargs.pop('fields')

        #if the key is start with '_', then remove it
        for k in kwargs.keys():
            if k.startswith('_'):
                kwargs.pop(k, None)

        if not isinstance(fields, (list, tuple)):
            raise ValueError("Index value format is not right, the value is %r" % indexes)

        props = []
        for y in fields:
            props.append(cls.c[y])

        Index(name, *props, **kwargs)

    return cls

def valid_model(model, engine_name=None):
    if isinstance(model, type) and issubclass(model, Model):
        return True
    if engine_name:
        engine = engine_manager[engine_name]
        return model in engine.models
    else:
        return True
    
def check_model_class(model_cls):
#    """
#    :param model: Model instance
#    Model.__engines__ could be a list, so if there are multiple then use
#    the first one
#    """

    #check dynamic flag
    if getattr(model_cls, "__dynamic__", False):
        return True

    #check the model_path
    model_path = model_cls.__module__ + '.' + model_cls.__name__
    _path = __models__.get(model_cls.tablename, {}).get('model_path', '')
    if _path and model_path != _path:
        return False
    return True
    
def find_metadata(model):
    """
    :param model: Model instance
    """
    engine_name = model.get_engine_name()
    engine = engine_manager[engine_name]
    return engine.metadata
    
def get_model(model, engine_name=None, signal=True, reload=False):
    """
    Return a real model object, so if the model is already a Model class, then
    return it directly. If not then import it.

    if engine_name is None, then if there is multi engines defined, it'll use
    'default', but if there is only one engine defined, it'll use this one

    :param dispatch: Used to switch dispatch signal
    """
    if isinstance(model, type) and issubclass(model, Model):
        return model
    if not isinstance(model, (str, unicode)):
        raise Error("Model %r should be string or unicode type" % model)
    
    #make model name is lower case
    model = model.lower()
    model_item = __models__.get(model)
    if not model_item:
        model_item = dispatch.get(None, 'find_model', model_name=model)
    if model_item:
        if not engine_name:
            #search according model_item, and it should has only one engine defined
            engines = model_item['engines']
            if len(engines) > 1:
                engine_name = __default_engine__
            else:
                engine_name = engines[0]
        engine = engine_manager[engine_name]

        item = engine._models.get(model)
        #process duplication
        if not item and engine.options.duplication:
            _item = engine.models.get(model)
            if _item:
                item = _item.copy()
                item['model'] = None
                engine._models[model] = item
        if item:
            loaded = False #True, model is already loaded, so consider if it needs be cached
            m = item['model']
            m_config = __models__[model].get('config', {})
            if isinstance(m, type) and issubclass(m, Model):
                loaded = True
                if reload:
                    loaded = False
                #add get_model previous hook
                if signal:
                    model_inst = dispatch.get(None, 'get_model', model_name=model, model_inst=m,
                                      model_info=item, model_config=m_config) or m
                    if m is not model_inst:
                        loaded = False
                else:
                    model_inst = m
            else:
                #add get_model previous hook
                if signal:
                    model_inst = dispatch.get(None, 'get_model', model_name=model, model_inst=None,
                                      model_info=item, model_config=m_config)
                else:
                    model_inst = None
                if not model_inst:
                    if item['model_path']:
                        mod_path, name = item['model_path'].rsplit('.', 1)
                        mod = __import__(mod_path, fromlist=['*'])
                        model_inst = getattr(mod, name)
                    #empty model_path means dynamic model
                if not model_inst:
                    raise ModelNotFound("Can't found the model %s in engine %s" % (model, engine_name))

            if not loaded:
                if model_inst._bound_classname == model and not reload:
                    model_inst = model_inst._use(engine_name)
                    item['model'] = model_inst
                else:
                    config = __models__[model].get('config', {})
                    if config:
                        for k, v in config.items():
                            setattr(model_inst, k, v)
                    item['model'] = model_inst
                    model_inst._alias = model
                    model_inst._engine_name = engine_name

                    if __lazy_model_init__:
                        for k, v in model_inst.properties.items():
                            v.__property_config__(model_inst, k)

                #add bind process
                if reload:
                    reset = True
                else:
                    reset = False
                model_inst.bind(engine.metadata, reset=reset)

            #post get_model
            if signal:
                dispatch.call(None, 'post_get_model', model_name=model, model_inst=model_inst,
                                      model_info=item, model_config=m_config)
            return model_inst
            
    raise ModelNotFound("Can't found the model %s in engine %s" % (model, engine_name))
    
def get_object_id(engine_name, tablename, id):
    return 'OC:%s:%s:%s' % (engine_name, tablename, str(id))

def get_object(table, id=None, condition=None, cache=False, fields=None, use_local=False,
               engine_name=None, session=None):
    """
    Get obj in Local.object_caches first and also use get(cache=True) function if 
    not found in object_caches
    """
    from uliweb import functions, settings
    
    model = get_model(table, engine_name)
        
    #if id is an object of Model, so get the real id value
    if isinstance(id, Model):
        return id
      
    if cache:
        if use_local:
            s = get_session(session)
            key = get_object_id(s.engine_name, model.tablename, id)
            value = s.get_local_cache(key)
            if value:
                return value
        obj = model.get(id, condition=condition, fields=fields, cache=True)
        if use_local:
            value = s.get_local_cache(key, obj)
    else:
        obj = model.get(id, condition=condition, fields=fields)
    
    return obj

def get_cached_object(table, id, condition=None, cache=True, fields=None, use_local=True, session=None):
    return get_object(table, id, condition, cache, fields, use_local, session)

class SQLMointor(object):
    def __init__(self, key_length=65, record_details=False):
        self.count = SortedDict()
        self.total = 0
        self.key_length = key_length
        self.details = []
        self.record_details = record_details
    
        def post_do(sender, query, conn, usetime, self=self):
            sql = str(query)
            c = self.count.setdefault(sql, {'count':0, 'time':0})
            c['count'] += 1
            c['time'] += usetime
            self.total += 1
            if self.record_details:
                self.details.append(rawsql(query))
                
        self.post_do = post_do
        
    def print_(self, message=''):
        print 
        print '====== sql execution count %d <%s> =======' % (self.total, message)
        for k, v in sorted(self.count.items(), key=lambda x:x[1]):
            k = k.replace('\r', '')
            k = k.replace('\n', '')
            if self.key_length and self.key_length>1 and len(k) > self.key_length:
                k = k[:self.key_length-3]+'...'
            if self.key_length > 0:
                format = "%%-%ds  %%3d  %%.3f" % self.key_length
            else:
                format = "%s  %3d  %.3f"
            print format % (k, v['count'], v['time'])
        if self.record_details:
            print '====== sql statements %d ====' % self.total
            for line in self.details:
                print '.', line
        print
        
    def close(self):
        self.count = {}
        self.total = 0
        self.details = []
        
def begin_sql_monitor(key_length=70, record_details=False):
    sql_monitor = SQLMointor(key_length, record_details)
    
    dispatch.bind('post_do')(sql_monitor.post_do)
    return sql_monitor
    
def close_sql_monitor(monitor):
    dispatch.unbind('post_do', monitor.post_do)
    monitor.close()

def reflect_table(tablename, engine_name='default'):
    from sqlalchemy.engine.reflection import Inspector
    from sqlalchemy import MetaData, Table

    if isinstance(engine_name, (str, unicode)):
        engine = engine_manager[engine_name].engine
    else:
        engine = engine_name
    if not isinstance(tablename, Table):
        meta = MetaData()
        table = Table(tablename, meta)
        insp = Inspector.from_engine(engine)
        insp.reflecttable(table, None)
        return table
    else:
        return tablename

def reflect_table_data(table, mapping=None, engine_name='default'):
    """
    Write table to Model dict
    """
    table = reflect_table(table, engine_name)
    mapping = mapping or {}

    from uliweb.utils.sorteddict import SortedDict

    field_type_map = {'VARCHAR':'str', 'VARCHAR2':'str', 'INTEGER':'int', 'FLOAT':'float'}

    meta = {}
    columns = SortedDict()
    #write columns
    _primary_key = None
    for k, v in table.columns.items():
        column_type = v.type
        type_name = column_type.__class__.__name__.lower()
        kwargs = SortedDict()
        field_type = type_name.upper()

        if type_name in ('char', 'varchar'):
            kwargs['max_length'] = column_type.length
        elif type_name in ('text', 'blob', 'integer', 'float', 'bigint'):
            pass
        elif type_name in ('clob',):
            field_type = 'TEXT'
        elif type_name in ('decimal', 'float'):
            kwargs['precision'] = v.type.precision
            kwargs['scale'] = v.type.scale
        elif type_name == 'number':
            if v.type.scale:
                kwargs['precision'] = v.type.precision
                kwargs['scale'] = v.type.scale
                field_type = 'DECIMAL'
            else:
                field_type = 'int'
        elif type_name == 'numeric':
            field_type = 'DECIMAL'
            kwargs['precision'] = v.type.precision
            kwargs['scale'] = v.type.scale
        elif type_name in ('timestamp',):
            field_type = 'DATETIME'
        elif type_name in ('datetime', 'date', 'time'):
            pass
        #for tinyint will be treated as bool
        elif type_name in ('tinyint', 'boolean'):
            field_type = 'bool'
        else:
            raise ValueError("Don't support column [{0}] for type [{1}] when parsing {2}".format(k, type_name, table.name))

        if v.primary_key:
            kwargs['primary_key'] = True
            _primary_key = k
            if v.autoincrement:
                kwargs['autoincrement'] = True
        if not v.nullable:
            kwargs['nullable'] = False
        if v.server_default:
            server_default = eval(str(v.server_default.arg))
            kwargs['server_default'] = server_default
        if v.index:
            kwargs['index'] = True
        if v.unique:
            kwargs['unique'] = True

        #convert field_type to common python data type
        field_type = field_type_map.get(field_type, field_type)
        columns[k] = field_type, kwargs

    meta['columns'] = columns

    indexes = []
    indexes_names = []
    for index in table.indexes:
        cols = list(index.columns)
        _len = len(cols)
        #if only one column it'll be set to Property
        if _len == 1:
            column_name = cols[0].name
            d = {'index':True}
            if index.unique:
                d['unique'] = index.unique
            columns[column_name][1].update(d)
        else:
            if not index.name in indexes_names:
                indexes.append({'name':index.name, 'columns':[x.name for x in index.columns],
                            'unique':index.unique})
                indexes_names.append(index.name)

    meta['indexes'] = indexes
    return meta

def reflect_table_model(table, mapping=None, without_id=False, engine_name='default'):
    """
    Write table to Model class
    """
    table = reflect_table(table, engine_name)
    mapping = mapping or {}
    meta = reflect_table_data(table)

    code = ['class {}(Model):'.format(table.name.title())]
    code.append('''    """
    Description:
    """

    __tablename__ = '{}\''''.format(table.name))

    #process id
    if 'id' not in meta['columns'] and without_id:
        code.append('    __without_id__ = True\n')
    # if _primary_key:
    #     code.append('    _primary_field = {}'.format(_primary_key))
        
    #output columns text
    for k, v in meta['columns'].items():
        kw = v[1].items()
        x_v = mapping.get(v[0])
        if x_v:
            kw.append(('type_class', x_v))
        kwargs = ', '.join([v[0]] + ['{0}={1!r}'.format(x, y) for x, y in kw])
        txt = " "*4 + "{0} = Field({1})".format(k, kwargs)
        code.append(txt)

    #output index text
    if meta['indexes']:
        code.append("""
    @classmethod
    def OnInit(cls):""")
    for index in meta['indexes']:
        buf = []
        buf.append(index['name'])
        for c in index['columns']:
            buf.append('cls.c.{}'.format(c))
        if index['unique']:
            buf.append('unique=True')
        code.append(' '*8 + 'Index({})'.format(', '.join(buf)))

    return '\n'.join(code)

def get_migrate_script(context, tables, metadata, engine_name=None):
    from alembic.autogenerate.api import compare_metadata, _produce_net_changes, \
        _autogen_context, _indent, _produce_upgrade_commands, _compare_tables
    from sqlalchemy.engine.reflection import Inspector


    diffs = []
    engine = engine_manager[engine_name]

    imports = set()

    autogen_context, connection = _autogen_context(context, imports)

    #init autogen_context
    autogen_context['opts']['sqlalchemy_module_prefix'] = 'sa.'
    autogen_context['opts']['alembic_module_prefix'] = 'op.'

    inspector = Inspector.from_engine(connection)

    _tables = set(inspector.get_table_names()) & set(tables)
    conn_table_names = set(zip([None] * len(_tables), _tables))

    for t in tables:
        m = engine.models.get(t)
        if m and not m['model']:
            get_model(t, engine_name, signal=False)

    metadata_table_names = set(zip([None] * len(tables), tables))

    _compare_tables(conn_table_names, metadata_table_names,
                    (),
                    inspector, metadata, diffs, autogen_context, False)

    script = """
def upgrade():
    """  + _indent(_produce_upgrade_commands(diffs, autogen_context)) + """
upgrade()
"""
    script = """
import sqlalchemy as sa
%s
""" % '\n'.join(list(imports)) + script
    return script

def run_migrate_script(context, script):
    import logging
    from alembic.operations import Operations

    log = logging.getLogger(__name__)
    op = Operations(context)
    code = compile(script, '<string>', 'exec', dont_inherit=True)
    env = {'op':op}
    log.debug(script)
    exec code in env

def migrate_tables(tables, engine_name=None):
    """
    Used to migrate dynamic table to database
    :param tables: tables name list, such as ['user']
    """
    from alembic.migration import MigrationContext
    engine = engine_manager[engine_name]
    mc = MigrationContext.configure(engine.session().connection)
    script =  get_migrate_script(mc, tables, engine.metadata)
    run_migrate_script(mc, script)

class ModelMetaclass(type):
    def __init__(cls, name, bases, dct):
        super(ModelMetaclass, cls).__init__(name, bases, dct)
        if name == 'Model':
            return
        cls._set_tablename()

        cls.properties = {}
        cls._fields_list = []
        cls._collection_names = {}

        defined = set()
        _primary_keys = []
        is_replace = dct.get('__replace__')
        for base in bases:
            if not hasattr(cls, '_primary_field') and hasattr(base, '_primary_field'):
                cls._primary_field = base._primary_field
            if hasattr(base, 'properties') and not is_replace:
                cls.properties.update(base.properties)
                if cls._primary_field in cls.properties:
                    _primary_keys.append(cls._primary_field)


        is_config = dct.get('__config__', True)
        cls._manytomany = {}
        cls._onetoone = {}
        for attr_name in dct.keys():
            attr = dct[attr_name]
            if isinstance(attr, Property):
                cls.add_property(attr_name, attr, set_property=False, config=not __lazy_model_init__)
                
                if isinstance(attr, ManyToMany):
                    cls._manytomany[attr_name] = attr

                #process primary
                #remove attr_name first if it's in _primary_keys
                if attr_name in _primary_keys:
                    _primary_keys.remove(attr_name)
                if 'primary_key' in attr.kwargs:
                    _primary_keys.append(attr_name)
                elif cls._primary_field and cls._primary_field == attr_name:
                    _primary_keys.append(attr_name)

         
        #if there is already defined primary_key, the id will not be primary_key
        #enable multi primary
        #has_primary_key = bool([v for v in cls.properties.itervalues() if 'primary_key' in v.kwargs])
        
        #add __without_id__ attribute to model, if set it, uliorm will not
        #create 'id' field for the model
        #if there is already has primary key, then id will not created 
        #change in 0.2.6 version
        without_id = getattr(cls, '__without_id__', False)
        if 'id' not in cls.properties and not without_id and len(_primary_keys)==0:
            cls.properties['id'] = f = Field(PKTYPE(), autoincrement=True, 
                primary_key=True, default=None, nullable=False, server_default=None)
            if not __lazy_model_init__:
                f.__property_config__(cls, 'id')
            setattr(cls, 'id', f)

            _primary_keys.append('id')

        #check if primary is more than one
        if len(_primary_keys) > 1:
            raise BadPropertyTypeError("Primary field chould be only one support, but {!r} found".format(_primary_keys))
        else:
            if len(_primary_keys) == 1:
                #set _key as primary property
                _p_key = _primary_keys[0]
                cls._key = getattr(cls, _p_key)
                cls._primary_field = _p_key

        fields_list = [(k, v) for k, v in cls.properties.items()]
        fields_list.sort(lambda x, y: cmp(x[1].creation_counter, y[1].creation_counter))
        cls._fields_list = fields_list
        
        #check if cls is matched with __models__ module_path
        if not check_model_class(cls):
            return

        if cls._bind and not __lazy_model_init__:
            cls.bind(auto_create=__auto_create__)
        
class LazyValue(object):
    def __init__(self, name, property):
        self.name = name
        self.property = property
        
    def __get__(self, model_instance, model_class):
        if model_instance is None:
            return self
        
        return self.property.get_lazy(model_instance, self.name, self.property.default)

    def __set__(self, model_instance, value):
        if model_instance is None:
            return
        
        setattr(model_instance, self.name, value)
        
class Property(object):
    data_type = str
    field_class = String
    type_name = 'str'
    creation_counter = 0
    property_type = 'column'   #Property type: 'column', 'compound', 'relation'
    server_default = None
    
    def __init__(self, label=None, verbose_name=None, fieldname=None, default=None,
        required=False, validators=None, choices=None, max_length=None, 
        hint='', auto=None, auto_add=None, type_class=None, type_attrs=None, 
        placeholder='', extra=None,
        sequence=False, **kwargs):
        self.label = label or verbose_name
        self.verbose_name = label or verbose_name
        self.property_name = None
        self.name = None
        self.fieldname = fieldname
        self.default = default
        self.required = required
        self.auto = auto
        self.auto_add = auto_add
        self.validators = validators or []
        self.hint = hint
        if not isinstance(self.validators, (tuple, list)):
            self.validators = [self.validators]
        self.choices = choices
        self.max_length = max_length
        self.kwargs = kwargs
        self.sequence = sequence
        self.creation_counter = Property.creation_counter
        self.value = None
        self.placeholder = placeholder
        self.extra = extra or {}
        self.type_attrs = type_attrs or {}
        self.type_class = type_class or self.field_class
        Property.creation_counter += 1
        
    def get_parameters(self):
        """
        Get common attributes and it'll used for Model.relationship clone process
        """
        d = {}
        for k in ['label', 'verbose_name', 'required', 'hint', 'placeholder', 'choices',
            'default', 'validators', 'max_length']:
            d[k] = getattr(self, k)
        return d

    def _get_column_info(self, kwargs):
        kwargs['primary_key'] = self.kwargs.get('primary_key', False)
        kwargs['autoincrement'] = self.kwargs.get('autoincrement', False)
        kwargs['index'] = self.kwargs.get('index', False)
        kwargs['unique'] = self.kwargs.get('unique', False)
        #nullable default change to False
        #primary key will not nullable by default 2015/12/1 limodou
        if kwargs['primary_key']:
            kwargs['nullable'] = False
        else:
            kwargs['nullable'] = self.kwargs.get('nullable', __nullable__)
        if __server_default__:
            kwargs['server_default' ] = self.kwargs.get('server_default', self.server_default)
        else:
            v = self.kwargs.get('server_default', None)
            if v is not None and isinstance(v, (int, long)):
                v = text(str(v))
            kwargs['server_default' ] = v

    def create(self, cls):
        global __nullable__
        
        kwargs = self.kwargs.copy()
        kwargs['key'] = self.name
        self._get_column_info(kwargs)

        f_type = self._create_type()
        args = ()
        if self.sequence:
            args = (self.sequence, )

        # return Column(self.property_name, f_type, *args, **kwargs)
        return Column(self.fieldname, f_type, *args, **kwargs)

    def _create_type(self):
        if self.max_length:
            f_type = self.type_class(self.max_length, **self.type_attrs)
        else:
            f_type = self.type_class(**self.type_attrs)
        return f_type
    
    def __property_config__(self, model_class, property_name):
        self.model_class = model_class
        self.property_name = property_name
        self.name = property_name
        if not self.fieldname:
            self.fieldname = property_name
        setattr(model_class, self._lazy_value(), LazyValue(self._attr_name(), self))
        
    def get_attr(self, model_instance, name, default):
        v = None
        if hasattr(model_instance, name):
            v = getattr(model_instance, name)
        if v is None:
            if callable(default):
                v = default()
            else:
                v = default
        return v
    
    def get_lazy(self, model_instance, name, default=None):
        v = self.get_attr(model_instance, name, default)
        if v is Lazy:
            _key = getattr(model_instance, model_instance._primary_field)
            if not _key:
                raise BadValueError('Instance is not a validate object of Model %s, ID property is not found' % model_class.__name__)
            model_instance.refresh()
            v = self.get_attr(model_instance, name, default)
        return v
        
    def __get__(self, model_instance, model_class):
        if model_instance is None:
            return self

        try:
            return self.get_lazy(model_instance, self._attr_name(), self.default)
        except AttributeError:
            return None
        
    def __set__(self, model_instance, value):
        if model_instance is None:
            return
        value = self.validate(value)
        #add value to model_instance._changed_value, so that you can test if
        #a object really need to save
        setattr(model_instance, self._attr_name(), value)

    def default_value(self):
        if callable(self.default):
            d = self.default()
        else:
            d = self.default
        return d
    
    def get_choices(self):
        if callable(self.choices):
            choices = self.choices()
        else:
            choices = self.choices
        return choices or []
        
    def get_display_value(self, value):
        if value is None:
            return ''
        if self.choices:
            v = dict(self.get_choices()).get(value, '')
            if isinstance(v, str):
                v = unicode(v, __default_encoding__)
            return v
        else:
            if isinstance(value, Model):
                return unicode(value)
            else:
                return self.to_unicode(value)

    def _validate(self, value, from_dump=False):
        if self.empty(value):
            if self.required:
                raise BadValueError('Property "%s" of Model [%s] is required, but %r found' % (self.name, self.model_class.__name__, value))
        #skip Lazy value
        if value is Lazy:
            return value
        
        try:
            if from_dump:
                value = self.convert_dump(value)
            else:
                value = self.convert(value)
        except TypeError as err:
            raise BadValueError('Property %s must be convertible to %s, but the value is (%s)' % (self.name, self.data_type, err))
        if hasattr(self, 'custom_validate'):
            value = self.custom_validate(value)
                
        for v in self.validators:
            v(value)
        return value

    def validate(self, value):
        return self._validate(value)
    
    def validate_dump(self, value):
        return self._validate(value, from_dump=True)

    def empty(self, value):
        return (value is None) or (isinstance(value, (str, unicode)) and not value.strip())

    def get_value_for_datastore(self, model_instance):
        return getattr(model_instance, self._attr_name(), None)

    def make_value_from_datastore(self, value):
        return value
    
    def convert(self, value):
        if self.data_type and not isinstance(value, self.data_type):
            return self.data_type(value)
        else:
            return value
    
    def convert_dump(self, value):
        return self.convert(value)
    
    def __repr__(self):
        return ("<%s 'type':%r, 'verbose_name':%r, 'name':%r, 'fieldname':%r, "
            "'default':%r, 'required':%r, 'validator':%r, "
            "'chocies':%r, 'max_length':%r, 'kwargs':%r>"
            % (
            self.__class__.__name__,
            self.data_type, 
            self.verbose_name,
            self.name,
            self.fieldname,
            self.default,
            self.required,
            self.validators,
            self.choices,
            self.max_length,
            self.kwargs)
            )
            
    def _attr_name(self):
        return '_STORED_' + self.name + '_'
    
    def _lazy_value(self):
        return '_' + self.name + '_'
    
    def to_str(self, v):
        if isinstance(v, unicode):
            return v.encode(__default_encoding__)
        elif isinstance(v, str):
            return v
        else:
            if v is None:
                return ''
            return str(v)
        
    def to_unicode(self, v):
        if isinstance(v, str):
            return unicode(v, __default_encoding__)
        elif isinstance(v, unicode):
            return v
        else:
            if v is None:
                return u''
            return unicode(v)

    def to_column_info(self):
        d = {}
        d['verbose_name'] = self.verbose_name or ''
        d['label'] = self.label or ''
        d['name'] = self.name
        d['fieldname'] = self.fieldname
        d['type'] = self.type_name
        d['type_name'] = self.get_column_type_name()
        d['relation'] = ''
        if isinstance(self, Reference):
            d['relation'] = '%s(%s:%s)' % (self.type_name, self.reference_class.__name__, self.reference_fieldname)
        self._get_column_info(d)
        return d

    def get_column_type_name(self):
        return self.type_name

class CharProperty(Property):
    data_type = unicode
    field_class = CHAR
    server_default=''
    type_name = 'CHAR'
    
    def __init__(self, label=None, default=u'', max_length=None, **kwds):
        if __check_max_length__ and not max_length:
            raise BadPropertyTypeError("max_length parameter not passed for property %s" % self.__class__.__name__)
        max_length = max_length or 255
        super(CharProperty, self).__init__(label, default=default, max_length=max_length, **kwds)
    
    def convert(self, value):
        if value is None:
            return u''
        if isinstance(value, str):
            return unicode(value, __default_encoding__)
        else:
            return self.data_type(value)
    
    def _create_type(self):
        if self.max_length:
            f_type = self.type_class(self.max_length, convert_unicode=True, **self.type_attrs)
        else:
            f_type = self.type_class(**self.type_attrs)
        return f_type
    
    def to_str(self, v):
        return safe_str(v)

    def get_column_type_name(self):
        return '%s(%d)' % (self.type_name, self.max_length)

class StringProperty(CharProperty):
    type_name = 'VARCHAR'
    field_class = VARCHAR

class BinaryProperty(CharProperty):
    type_name = 'BINARY'
    field_class = BINARY
    data_type = str

    def _create_type(self):
        if self.max_length:
            f_type = self.type_class(self.max_length, **self.type_attrs)
        else:
            f_type = self.type_class(**self.type_attrs)
        return f_type

class VarBinaryProperty(BinaryProperty):
    type_name = 'VARBINARY'
    field_class = VARBINARY

class UUIDBinaryProperty(VarBinaryProperty):
    type_name = 'UUID_B'
    field_class = VARBINARY

    def __init__(self, **kwds):
        kwds['max_length'] = 16
        super(UUIDBinaryProperty, self).__init__(**kwds)
        self.auto_add = True

    def default_value(self):
        import uuid

        u = uuid.uuid4()
        return u.get_bytes()

    def convert(self, value):
        if value is None:
            return ''
        return value

class UUIDProperty(StringProperty):
    type_name = 'UUID'
    field_class = VARCHAR

    def __init__(self, **kwds):
        kwds['max_length'] = 32
        super(UUIDProperty, self).__init__(**kwds)
        self.auto_add = True

    def default_value(self):
        import uuid

        u = uuid.uuid4()
        return u.get_hex()[:self.max_length]

    def convert(self, value):
        if value is None:
            return ''
        return value

class FileProperty(StringProperty):
    def __init__(self, label=None, max_length=None, upload_to=None, upload_to_sub=None, **kwds):
        max_length = max_length or 255
        super(FileProperty, self).__init__(label, max_length=max_length, **kwds)
        self.upload_to = upload_to
        self.upload_to_sub = upload_to_sub
        
class UnicodeProperty(StringProperty):
    pass
    
class TextProperty(Property):
    field_class = Text
    data_type = unicode
    type_name = 'TEXT'

    def __init__(self, label=None, default=u'', **kwds):
        super(TextProperty, self).__init__(label, default=default, max_length=None, **kwds)
    
    def convert(self, value):
        if not value:
            return u''
        if isinstance(value, str):
            return unicode(value, __default_encoding__)
        else:
            return self.data_type(value)
    
class BlobProperty(Property):
    field_class = BLOB
    data_type = str
    type_name = 'BLOB'
    
    def __init__(self, label=None, default='', **kwds):
        super(BlobProperty, self).__init__(label, default=default, max_length=None, **kwds)
    
    def get_display_value(self, value):
        return repr(value)
    
    def convert(self, value):
        if not value:
            return ''
        return value
    
class PickleProperty(BlobProperty):
    field_class = PickleType
    data_type = None
    type_name = 'PICKLE'
    
    def to_str(self, v):
        return pickle.dumps(v, pickle.HIGHEST_PROTOCOL)
    
    def convert_dump(self, v):
        return pickle.loads(v)

    def convert(self, value):
        return value
    
class JsonProperty(TextProperty):
    field_class = TEXT
    data_type = None
    type_name = 'JSON'

    def get_value_for_datastore(self, model_instance):
        from uliweb import json_dumps
        return json_dumps(getattr(model_instance, self._attr_name(), None))

    def make_value_from_datastore(self, value):
        return self.convert_dump(value)

    def convert_dump(self, v):
        import json
        if v:
            return json.loads(v)

    def convert(self, value):
        return value

class DateTimeProperty(Property):
    data_type = datetime.datetime
    field_class = DateTime
    server_default = '0000-00-00 00:00:00'
    type_name = 'DATETIME'
    
    def __init__(self, label=None, auto_now=False, auto_now_add=False,
            format=None, **kwds):
        super(DateTimeProperty, self).__init__(label, **kwds)
        self.auto_now = auto_now
        self.auto_now_add = auto_now_add
        self.format = format

    def custom_validate(self, value):
        if value and not isinstance(value, self.data_type):
            raise BadValueError('Property %s must be a %s' %
                (self.name, self.data_type.__name__))
        return value
    
    @staticmethod
    def now():
        return _date.now()

    def make_value_from_datastore(self, value):
        if value is not None:
            value = self._convert_func(value)
        return value

    @staticmethod
    def _convert_func(*args, **kwargs):
        return _date.to_datetime(*args, **kwargs)
    
    def convert(self, value):
        if not value:
            return None
        d = self._convert_func(value, format=self.format)
        if d:
            return d
        raise BadValueError('The datetime value is not a valid format')
    
    def to_str(self, v):
        if isinstance(v, self.data_type):
            return _date.to_string(v, timezone=False)
        else:
            if not v:
                return ''
            return str(v)
    
    def to_unicode(self, v):
        if isinstance(v, self.data_type):
            return unicode(_date.to_string(v, timezone=False))
        else:
            if not v:
                return u''
            return unicode(v)

class DateProperty(DateTimeProperty):
    data_type = datetime.date
    field_class = Date
    server_default = '0000-00-00'
    type_name = 'DATE'
    
    @staticmethod
    def _convert_func(*args, **kwargs):
        return _date.to_date(*args, **kwargs)
    
    @staticmethod
    def now():
        return _date.to_date(_date.now())
    
class TimeProperty(DateTimeProperty):
    data_type = datetime.time
    field_class = Time
    server_default = '00:00:00'
    type_name = 'TIME'
    
    @staticmethod
    def _convert_func(*args, **kwargs):
        return _date.to_time(*args, **kwargs)
    
    @staticmethod
    def now():
        return _date.to_time(_date.now())
    
class IntegerProperty(Property):
    """An integer property."""

    data_type = int
    field_class = Integer
    server_default=text('0')
    type_name = 'INTEGER'
    
    def __init__(self, label=None, default=0, **kwds):
        super(IntegerProperty, self).__init__(label, default=default, **kwds)
    
    def convert(self, value):
        if value == '':
            return 0
        if value is None:
            return value
        return self.data_type(value)
        
    def custom_validate(self, value):
        if value and not isinstance(value, (int, long, bool)):
            raise BadValueError('Property %s must be an int, long or bool, not a %s'
                % (self.name, type(value).__name__))
        return value

class BigIntegerProperty(IntegerProperty):
    field_class = BigInteger
    type_name = 'BIGINT'
    
class SmallIntegerProperty(IntegerProperty):
    field_class = SmallInteger
    type_name = 'SMALLINT'

class FloatProperty(Property):
    """A float property."""

    data_type = float
    field_class = Float
    server_default=text('0')
    type_name = 'FLOAT'
    
    def __init__(self, label=None, default=0.0, precision=None, **kwds):
        super(FloatProperty, self).__init__(label, default=default, **kwds)
        self.precision = precision
        
    def _create_type(self):
        f_type = self.type_class(precision=self.precision, **self.type_attrs)
        return f_type
    
    def convert(self, value):
        if value == '' or value is None:
            return 0.0
        return self.data_type(value)

    def custom_validate(self, value):
        if value and not isinstance(value, float):
            raise BadValueError('Property %s must be a float, not a %s' 
                % (self.name, type(value).__name__))
        if abs(value) < __zero_float__:
            value = 0.0
        return value

    def get_column_type_name(self):
        return '%s' % self.type_name

class DecimalProperty(Property):
    """A float property."""

    data_type = decimal.Decimal
    field_class = Numeric
    server_default=text('0.00')
    type_name = 'DECIMAL'
    
    def __init__(self, label=None, default='0.0', precision=10, scale=2, **kwds):
        super(DecimalProperty, self).__init__(label, default=default, **kwds)
        self.precision = precision
        self.scale = scale
   
    def convert(self, value):
        if value == '' or value is None:
            return decimal.Decimal('0.0')
        return self.data_type(value)

    def _create_type(self):
        f_type = self.type_class(precision=self.precision, scale=self.scale, **self.type_attrs)
        return f_type
    
    def get_display_value(self, value):
        if value is None:
            return ''
        if self.choices:
            v = dict(self.get_choices()).get(str(value), '')
            if isinstance(v, str):
                v = unicode(v, __default_encoding__)
            return v
        else:
            return str(value)

    def get_column_type_name(self):
        return '%s(%d,%d)' % (self.type_name, self.precision, self.scale)

class BooleanProperty(Property):
    """A boolean property."""

    data_type = bool
    field_class = Boolean
    server_default=text('0')
    type_name = 'BOOL'
    
    def __init__(self, label=None, default=False, **kwds):
        super(BooleanProperty, self).__init__(label, default=default, **kwds)
    
    def custom_validate(self, value):
        if value is not None and not isinstance(value, bool):
            raise BadValueError('Property %s must be a boolean, not a %s' 
                % (self.name, type(value).__name__))
        return value

    def convert(self, value):
        if not value:
            return False
        if value in ['1', 'True', 'true', True]:
            return True
        else:
            return False
        
class ReferenceProperty(Property):
    """A property that represents a many-to-one reference to another model.
    """
    data_type = int
    field_class = PKCLASS()
    type_name = 'Reference'

    def __init__(self, reference_class=None, label=None, collection_name=None,
        reference_fieldname=None, required=False, engine_name=None, **attrs):
        """Construct ReferenceProperty.

        Args:
            reference_class: Which model class this property references.
            verbose_name or label: User friendly name of property.
            collection_name: If provided, alternate name of collection on
                reference_class to store back references.    Use this to allow
                a Model to have multiple fields which refer to the same class.
            reference_fieldname used to specify which fieldname of reference_class
                should be referenced
        """
        super(ReferenceProperty, self).__init__(label, **attrs)

        self._collection_name = collection_name
        if reference_class and isinstance(reference_class, type) and issubclass(reference_class, Model):
            self.reference_fieldname = reference_fieldname or reference_class._primary_field
        else:
            self.reference_fieldname = reference_fieldname
        self.required = required
        self.engine_name = engine_name
        self.reference_class = reference_class

        if __lazy_model_init__:
            if inspect.isclass(self.reference_class) and issubclass(self.reference_class, Model):
                warnings.simplefilter('default')
                warnings.warn("Reference Model should be a string type, but [%s] model class found." % self.reference_class.__name__, DeprecationWarning)
        
    def create(self, cls):
        global __nullable__
        
        args = self.kwargs.copy()
        args['key'] = self.name
#        if not callable(self.default):
#        args['default'] = self.default
        args['primary_key'] = self.kwargs.get('primary_key', False)
        args['autoincrement'] = self.kwargs.get('autoincrement', False)
        args['index'] = self.kwargs.get('index', False)
        args['unique'] = self.kwargs.get('unique', False)
        args['nullable'] = self.kwargs.get('nullable', __nullable__)
        f_type = self._create_type()
        if __server_default__:
            #for int or long data_type, it'll automatically set text('0')
            if self.data_type is int or self.data_type is long :
                args['server_default'] = text('0')
            else:
                v = self.reference_field.kwargs.get('server_default')
                args['server_default'] = v
        return Column(self.fieldname, f_type, **args)
    
    def _create_type(self):
        if not hasattr(self.reference_class, self.reference_fieldname):
            raise KindError('reference_fieldname is not existed')
        self.reference_field = getattr(self.reference_class, self.reference_fieldname)
        
        #process data_type
        self.data_type = self.reference_field.data_type

        field_class = self.reference_field.field_class
        if self.reference_field.max_length:
            f_type = field_class(self.reference_field.max_length)
        else:
            f_type = field_class
        return f_type
    
    def __property_config__(self, model_class, property_name):
        """Loads all of the references that point to this model.
        """
        super(ReferenceProperty, self).__property_config__(model_class, property_name)

        if not (
                (isinstance(self.reference_class, type) and issubclass(self.reference_class, Model)) or
                self.reference_class is _SELF_REFERENCE or
                valid_model(self.reference_class, self.engine_name)):
            raise KindError('reference_class %r must be Model or _SELF_REFERENCE or available table name' % self.reference_class)
        
        if self.reference_class is _SELF_REFERENCE or self.reference_class is None:
            self.reference_class = model_class
        else:
            self.reference_class = get_model(self.reference_class, self.engine_name,
                                             signal=False)
        self.reference_fieldname = self.reference_fieldname or self.reference_class._primary_field
        self.collection_name = self.reference_class.get_collection_name(model_class.tablename, self._collection_name, model_class.tablename)
        setattr(self.reference_class, self.collection_name,
            _ReverseReferenceProperty(model_class, property_name, self._id_attr_name()))

    def __get__(self, model_instance, model_class):
        """Get reference object.

        This method will fetch unresolved entities from the datastore if
        they are not already loaded.

        Returns:
            ReferenceProperty to Model object if property is set, else None.
        """
        if model_instance is None:
            return self
        if hasattr(model_instance, self._attr_name()):
#            reference_id = getattr(model_instance, self._attr_name())
            reference_id = self.get_lazy(model_instance, self._attr_name(), None)
        else:
            reference_id = None
        if reference_id:
            #this will cache the reference object
            resolved = getattr(model_instance, self._resolved_attr_name())
            if resolved is not None:
                return resolved
            else:
                #change id_field to reference_fieldname
#                id_field = self._id_attr_name()
#                d = self.reference_class.c[id_field]
                d = self.reference_class.c[self.reference_fieldname]
                instance = self.reference_class.get(d==reference_id)
                if instance is None:
                    raise NotFound('ReferenceProperty %s failed to be resolved' % self.reference_fieldname, self.reference_class, reference_id)
                setattr(model_instance, self._resolved_attr_name(), instance)
                return instance
        else:
            return None
        
    def get_value_for_datastore(self, model_instance):
        if not model_instance:
            return None
        else:
            return getattr(model_instance, self._attr_name(), None)

    def __set__(self, model_instance, value):
        """Set reference."""
        value = self.validate(value)
        if value is not None:
            if not isinstance(value, Model):
                setattr(model_instance, self._attr_name(), value)
                setattr(model_instance, self._resolved_attr_name(), None)
            else:
                setattr(model_instance, self._attr_name(), getattr(value, self.reference_fieldname))
                setattr(model_instance, self._resolved_attr_name(), value)
        else:
            setattr(model_instance, self._attr_name(), None)
            setattr(model_instance, self._resolved_attr_name(), None)
        
    def validate(self, value):
        """Validate reference.

        Returns:
            A valid value.

        Raises:
            BadValueError for the following reasons:
                - Value is not saved.
                - Object not of correct model type for reference.
        """
        if value == '':
            if self.kwargs.get('nullable', __nullable__):
                value = None
            else:
                value = 0
            
        if not isinstance(value, Model):
            return super(ReferenceProperty, self).validate(value)

        if not value.is_saved():
            raise BadValueError(
                    '%s instance must be saved before it can be stored as a '
                    'reference' % self.reference_class.__class__.__name__)
        if not isinstance(value, self.reference_class):
            raise KindError('Property %s must be an instance of %s' %
                    (self.name, self.reference_class.__class__.__name__))

        return value

    validate_dump = validate
        
    def _id_attr_name(self):
        """Get attribute of referenced id.
        """
        return self.reference_fieldname

    def _resolved_attr_name(self):
        """Get attribute of resolved attribute.

        The resolved attribute is where the actual loaded reference instance is
        stored on the referring model instance.

        Returns:
            Attribute name of where to store resolved reference model instance.
        """
        return '_RESOLVED_' + self._attr_name()

    def convert(self, value):
        if value == '':
            return 0
        if value is None:
            return value
        return self.data_type(value)

    def get_column_type_name(self):
        return self.reference_field.get_column_type_name()

Reference = ReferenceProperty

class OneToOne(ReferenceProperty):
    type_name = 'OneToOne'

    def create(self, cls):
        global __nullable__
        
        args = self.kwargs.copy()
        args['key'] = self.name
#        if not callable(self.default):
#        args['default'] = self.default
        args['primary_key'] = self.kwargs.get('primary_key', False)
        args['autoincrement'] = self.kwargs.get('autoincrement', False)
        args['index'] = self.kwargs.get('index', True)
        args['unique'] = self.kwargs.get('unique', True)
        args['nullable'] = self.kwargs.get('nullable', __nullable__)
        f_type = self._create_type()
        if __server_default__:
            if self.data_type is int or self.data_type is long :
                args['server_default'] = text('0')
            else:
                args['server_default'] = self.reference_field.kwargs.get('server_default')
        return Column(self.fieldname, f_type, **args)

    def __property_config__(self, model_class, property_name):
        """Loads all of the references that point to this model.
        """
        
        #Direct invoke super with ReferenceProperty in order to skip the
        #ReferenceProperty process, but instead of invode ReferenceProperty's
        #parent function
        super(ReferenceProperty, self).__property_config__(model_class, property_name)
        if not (
                (isinstance(self.reference_class, type) and issubclass(self.reference_class, Model)) or
                self.reference_class is _SELF_REFERENCE or
                valid_model(self.reference_class, self.engine_name)):
            raise KindError('reference_class %r must be Model or _SELF_REFERENCE or available table name' % self.reference_class)
        
        if self.reference_class is _SELF_REFERENCE:
            self.reference_class = self.data_type = model_class
        else:
            self.reference_class = get_model(self.reference_class, self.engine_name,
                                             signal=False)
        self.reference_fieldname = self.reference_fieldname or self.reference_class._primary_field

        self.collection_name = self._collection_name
        if self.collection_name is None:
            self.collection_name = '%s' % (model_class.tablename)
        #enable reenter 2015/10/29
        # if hasattr(self.reference_class, self.collection_name):
        #     raise DuplicatePropertyError('Class %s already has property %s'
        #          % (self.reference_class.__name__, self.collection_name))
        setattr(self.reference_class, self.collection_name,
            _OneToOneReverseReferenceProperty(model_class, property_name,
                            self._id_attr_name(), self.collection_name))
        #append to reference_class._onetoone
        self.reference_class._onetoone[self.collection_name] = model_class

def get_objs_columns(objs, field=None, model=None):
    keys = []
    new_objs = []
    if isinstance(objs, (str, unicode)):
        objs = [x for x in objs.split(',')]
    for x in objs:
        if not x:
            continue
        if isinstance(x, (tuple, list)):
            new_objs.extend(x)
        else:
            new_objs.append(x)
            
    if model and field:
        prop = getattr(model, field)
    else:
        prop = None
    for o in new_objs:
        if not isinstance(o, Model):
            if prop:
                key = prop.validate(o)
            else:
                key = o
        else:
            key = o.get_datastore_value(field or o._primary_field)
        if key not in keys:
            keys.append(key)
    return keys

class Result(object):
    def __init__(self, model=None, condition=None, *args, **kwargs):
        self.model = model
        self.condition = condition
        self.columns = list(self.model.table.c)
        self.funcs = []
        self.args = args
        self.kwargs = kwargs
        self.result = None
        self.default_query_flag = True
        self._group_by = None
        self._having = None
        self.distinct_field = None
        self._values_flag = False
        self._join = []
        self._limit = None
        self._offset = None
        self.connection = model.get_session()
        
    def do_(self, query):
        global do_
        return do_(query, self.connection)
    
    def get_column(self, model, fieldname):
        if isinstance(fieldname, (str, unicode)):
            if issubclass(model, Model):
                v = fieldname.split('.')
                if len(v) > 1:
                    field = get_model(v[0], engine_name=self.model.get_engine_name(),
                                      signal=False).table.c(v[1])
                else:
                    field = model.table.c[fieldname]
            else:
                field = model.c[fieldname]
        else:
            field = fieldname
        return field
    
    def get_columns(self, model=None, columns=None):
        columns = columns or self.columns
        model = model or self.model
        fields = []
        field = None
        if self.distinct_field is not None:
            field = self.get_column(model, self.distinct_field)
            fields.append(func.distinct(field).label(field.name))
        for col in columns:
            if col is not field:
                fields.append(col)
        
        return fields
    
    def get_fields(self):
        """
        get property instance according self.columns
        """
        columns = self.columns
        model = self.model
        fields = []
        for col in columns:
            if isinstance(col, (str, unicode)):
                v = col.split('.')
                if len(v) > 1:
                    field = get_model(v[0], engine_name=self.model.get_engine_name(),
                                      signal=False).properties(v[1])
                else:
                    field = model.properties[col]
            elif isinstance(col, Column):
                field = get_model(col.table.name, engine_name=self.model.get_engine_name(),
                                  signal=False).properties[col.name]
            else:
                field = col
            
            fields.append(field)
        
        return fields
        
    def connect(self, connection):
        if connection:
            self.connection = connection
        return self
    use = connect
    
    def all(self):
        return self

    def empty(self):
        """
        return empty query set
        """
        return self.filter(false())

    def join(self, model, cond, isouter=False):
        _join = None
        model = get_model(model, engine_name=self.model.get_engine_name(),
                          signal=False)
        if issubclass(model, Model):
            # if cond is None:
            #     for prop in Model.proterties:
            #         if isinstance(prop, ReferenceProperty) and prop.reference_class is self.model:
            #             _right = prop.reference_class
            #             _join = self.model.table.join(_right.table,
            #                                           _right.c[prop.reference_fieldname])
            #             break
            # else:
            _join = self.model.table.join(model.table, cond, isouter=isouter)
            self._join.append(_join)
        else:
            raise BadValueError("Only Model support in this function.")
        return self

    def get(self, condition=None):
        if isinstance(condition, ColumnElement):
            self.filter(condition).one()
        else:
            self.filter(self.model.c[self._primary_field]==condition).one()

    def count(self):
        """
        If result is True, then the count will process result set , if
        result if False, then only use condition to count
        """
        if self._group_by or self._join:
            return self.do_(self.get_query().alias().count()).scalar()
        else:
            return self.do_(self.get_query().with_only_columns([func.count()]).limit(None).order_by(None).offset(None)).scalar()

    def any(self):
        row = self.do_(
            self.get_query().limit(1)
            )
        return len(list(row)) > 0

    def filter(self, *condition):
        """
        If there are multple condition, then treats them *and* relastion.
        """
        if not condition:
            return self
        cond = true()
        for c in condition:
            if c is not None:
                cond = and_(c, cond)
        if self.condition is not None:
            self.condition = and_(cond, self.condition)
        else:
            self.condition = cond
        return self
    
    def order_by(self, *args, **kwargs):
        self.funcs.append(('order_by', args, kwargs))
        return self
    
    def group_by(self, *args):
        self._group_by = args
        return self

    def having(self, *args):
        self._having = args
        return self

    def fields(self, *args, **kwargs):
        if args:
            args = flat_list(args)
            if args:
                if self.model._primary_field and self.model._primary_field not in args:
                    args.append(self.model._primary_field)
                self.funcs.append(('with_only_columns', ([self.get_column(self.model, x) for x in args],), kwargs))
        return self
        
    def values(self, *args, **kwargs):
        self.funcs.append(('with_only_columns', ([self.get_column(self.model, x) for x in args],), kwargs))
        self._values_flag = True
        return self
    
    def values_one(self, *args, **kwargs):
        self.funcs.append(('with_only_columns', ([self.get_column(self.model, x) for x in args],), kwargs))
        self.run(1)
        result = self.result.fetchone()
        return result

    def distinct(self, field=None):
        """
        If field is None, then it means that it'll create:
            select distinct *
        and if field is not None, for example: 'name', it'll create:
            select distinc(name), 
        """
        if field is None:
            self.funcs.append(('distinct', (), {}))
        else:
            self.distinct_field = field
        return self
    
    def limit(self, *args, **kwargs):
        self.funcs.append(('limit', args, kwargs))
        if args:
            self._limit = bool(args[0])
        else:
            self._limit = False
        return self

    def offset(self, *args, **kwargs):
        self._offset = True
        self.funcs.append(('offset', args, kwargs))
        return self
    
    def update(self, **kwargs):
        """
        Execute update table set field = field+1 like statement
        """
        if self.condition is not None:
            self.result = self.do_(self.model.table.update().where(self.condition).values(**kwargs))
        else:
            self.result = self.do_(self.model.table.update().values(**kwargs))
        return self.result
    
    def without(self, flag='default_query'):
        if flag == 'default_query':
            self.default_query_flag = False
        return self
    
    def run(self, limit=0):
        query = self.get_query()
        #add limit support
        if limit > 0:
            query = getattr(query, 'limit')(limit)
        self.result = self.do_(query)
        return self.result
    
    def save_file(self, filename, encoding='utf8', headers=None,
                  convertors=None, display=True, **kwargs):
        """
        save result to a csv file.
        display = True will convert value according choices value
        """
        global save_file
        
        convertors = convertors or {}
        
        if display:
            fields = self.get_fields()
            for i, column in enumerate(fields):
                if column.name not in convertors:
                    def f(value, data):
                        return column.get_display_value(value)
                    convertors[column.name] = f

        return save_file(self.run(), filename, encoding=encoding,
                         headers=headers, convertors=convertors, **kwargs)
    
    def get_query(self, columns=None):
        #user can define default_query, and default_query 
        #should be class method
        columns = columns or self.get_columns()
        
        if self.default_query_flag:
            _f = getattr(self.model, 'default_query', None)
            if _f:
                _f(self)
        from_ = self._join
        from_.append(self.model.table)
        if self.condition is not None:
            query = select(columns, self.condition, from_obj=from_, **self.kwargs)
        else:
            query = select(columns, from_obj=from_, **self.kwargs)

        for func, args, kwargs in self.funcs:
            query = getattr(query, func)(*args, **kwargs)
        if self._group_by:
            query = query.group_by(*self._group_by)
            if self._having:
                query = query.having(*self._having)
        return query

    def __str__(self):
        return rawsql(self.get_query())
    
    def load(self, values):
        if self._values_flag:
            return values
        else:
            return self.model.load(values.items())
        
    def for_update(self, flag=True):
        """
        please see http://docs.sqlalchemy.org/en/latest/core/expression_api.html search for update
        """
        self.kwargs['for_update'] = flag
        return self
    
    def one(self):
        self.run(1)
        if not self.result:
            return
        
        result = self.result.fetchone()
        if result:
            return self.load(result)
        
    first = one
    
    def clear(self):
        return do_(self.model.table.delete(self.condition), self.connection)
    
    remove = clear
            
    def __del__(self):
        if self.result:
            self.result.close()
            self.result = None

    def __iter__(self):
        self.result = self.run()
        while 1:
            result = self.result.fetchone()
            if not result:
                raise StopIteration
            yield self.load(result)
  
class ReverseResult(Result):
    def __init__(self, model, condition, a_field, b_table, instance, b_field, *args, **kwargs):
        self.model = model
        self.b_table = b_table
        self.b_field = b_field
        self.instance = instance
        self.condition = condition
        self.a_field = a_field
        self.columns = list(self.model.table.c)
        self.funcs = []
        self.args = args
        self.kwargs = kwargs
        self.result = None
        self.default_query_flag = True
        self._group_by = None
        self._having = None
        self._limit = None
        self._offset = None
        self._join = []
        self.distinct_field = None
        self._values_flag = False
        self.connection = model.get_session()
        
    def has(self, *objs):
        keys = get_objs_columns(objs)
        
        if not keys:
            return False

        return self.model.filter(self.condition, self.model.table.c[self.model._primary_field].in_(keys)).any()

    def ids(self):
        query = select([self.model.c['id']], self.condition)
        ids = [x[0] for x in self.do_(query)]
        return ids
    
    def keys(self):
        query = select([self.model.c[self.model._primary_field]], self.condition)
        keys = [x[0] for x in self.do_(query)]
        return keys

    def clear(self, *objs):
        """
        Clear the third relationship table, but not the ModelA or ModelB
        """
        if objs:
            keys = get_objs_columns(objs)
            self.do_(self.model.table.delete(self.condition & self.model.table.c[self.model._primary_field].in_(keys)))
        else:
            self.do_(self.model.table.delete(self.condition))
    
    remove = clear
    
class ManyResult(Result):
    def __init__(self, modela, instance, property_name, modelb, 
        table, fielda, fieldb, realfielda, realfieldb, valuea, through_model=None):
        """
        modela will define property_name = ManyToMany(modelb) relationship.
        instance will be modela instance
        """
        self.modela = modela
        self.instance = instance
        self.property_name = property_name
        self.modelb = modelb
        self.table = table  #third table
        self.fielda = fielda
        self.fieldb = fieldb
        self.realfielda = realfielda
        self.realfieldb = realfieldb
        self.valuea = valuea
        self.columns = list(self.modelb.table.c)
        self.condition = ''
        self.funcs = []
        self.result = None
        self.with_relation_name = None
        self.through_model = through_model
        self.default_query_flag = True
        self._group_by = None
        self._having = None
        self._join = []
        self._limit = None
        self._offset = None
        self.distinct_field = None
        self._values_flag = False
        self.connection = self.modela.get_session()
        self.kwargs = {}
        
    def all(self, cache=False):
        """
        can use cache to return objects
        """
        if cache:
            return [get_object(self.modelb, obj_id, cache=True, use_local=True) for obj_id in self.keys(True)]
        else:
            return self

    def get(self, condition=None):
        if not isinstance(condition, ColumnElement):
            return self.filter(self.modelb.c[self.realfieldb]==condition).one()
        else:
            return self.filter(condition).one()

    def add(self, *objs):
        new_objs = []
        for x in objs:
            if not x:
                continue
            if isinstance(x, (tuple, list)):
                new_objs.extend(x)
            else:
                new_objs.append(x)
        
        modified = False
        for o in new_objs:
            if not self.has(o):
                if isinstance(o, Model):
                    v = getattr(o, self.realfieldb)
                else:
                    v = o
                d = {self.fielda:self.valuea, self.fieldb:v}
                if self.through_model:
                    obj = self.through_model(**d)
                    obj.save()
                else:
                    self.do_(self.table.insert().values(**d))
                modified = modified or True
        
        #cache [] to _STORED_attr_name
        setattr(self.instance, self.store_key, Lazy)
        
        return modified
         
    @property
    def store_key(self):
        if self.property_name in self.instance.properties:
            return self.instance.properties[self.property_name]._attr_name()
        else:
            return '_CACHED_'+self.property_name
    
    def ids(self, cache=False):
        key = self.store_key
        ids = getattr(self.instance, key, None)
        if not cache or ids is None or ids is Lazy:
            if self.valuea is None:
                return []
            query = select([self.table.c[self.fieldb]], self.table.c[self.fielda]==self.valuea)
            ids = [x[0] for x in self.do_(query)]
        if cache:
            setattr(self.instance, key, ids)
        return ids
    
    def keys(self, cache=False):
        key = self.store_key
        keys = getattr(self.instance, key, None)
        if not cache or keys is None or keys is Lazy:
            if self.valuea is None:
                return []
            query = select([self.table.c[self.fieldb]], self.table.c[self.fielda]==self.valuea)
            keys = [x[0] for x in self.do_(query)]
        if cache:
            setattr(self.instance, key, keys)
        return keys

    def update(self, *objs):
        """
        Update the third relationship table, but not the ModelA or ModelB
        """
        keys = self.keys()
        new_keys = get_objs_columns(objs, self.realfieldb)

        modified = False
        for v in new_keys:
            if v in keys:    #the id has been existed, so don't insert new record
                keys.remove(v)
            else:
                d = {self.fielda:self.valuea, self.fieldb:v}
                if self.through_model:
                    obj = self.through_model(**d)
                    obj.save()
                else:
                    self.do_(self.table.insert().values(**d))
                modified = True
                
        if keys: #if there are still keys, so delete them
            self.clear(*keys)
            modified = True
        
        #cache [] to _STORED_attr_name
        setattr(self.instance, self.store_key, new_keys)
        
        return modified
            
    def clear(self, *objs):
        """
        Clear the third relationship table, but not the ModelA or ModelB
        """
        if objs:
            keys = get_objs_columns(objs, self.realfieldb)
            self.do_(self.table.delete((self.table.c[self.fielda]==self.valuea) & (self.table.c[self.fieldb].in_(keys))))
        else:
            self.do_(self.table.delete(self.table.c[self.fielda]==self.valuea))
        #cache [] to _STORED_attr_name
        setattr(self.instance, self.store_key, Lazy)
        
    remove = clear
    
    def count(self):
        if self._group_by or self._join:
            return self.do_(self.get_query().alias().count()).scalar()
        else:
            return self.do_(
                self.get_query().with_only_columns([func.count()]).limit(None).order_by(None).offset(None)
                ).scalar()
    
    def any(self):
        row = self.do_(
            select([self.table.c[self.fieldb]], 
                (self.table.c[self.fielda]==self.valuea) &
                self.condition).limit(1)
            )
        return len(list(row)) > 0

    def has(self, *objs):
        keys = get_objs_columns(objs, self.realfieldb)
        
        if not keys:
            return False
        
        row = self.do_(select([text('*')], 
            (self.table.c[self.fielda]==self.valuea) & 
            (self.table.c[self.fieldb].in_(keys))).limit(1))
        return len(list(row)) > 0
        
    def fields(self, *args, **kwargs):
        if args:
            args = flat_list(args)
            if args:
                if self.modelb._primary_field and self.modelb._primary_field not in args:
                    args.append(self.modelb.c[self.modelb._primary_field])
                self.funcs.append(('with_only_columns', ([self.get_column(self.modelb, x) for x in args],), kwargs))
        return self

    def values(self, *args, **kwargs):
        self.funcs.append(('with_only_columns', ([self.get_column(self.modelb, x) for x in args],), kwargs))
        self._values_flag = True
        return self

    def values_one(self, *args, **kwargs):
        self.funcs.append(('with_only_columns', ([self.get_column(self.modelb, x) for x in args],), kwargs))
        self.run(1)
        result = self.result.fetchone()
        return result

    def with_relation(self, relation_name=None):
        """
        if relation is not None, when fetch manytomany result, also
        fetch relation record and saved them to manytomany object,
        and named them as relation.
        
        If relation_name is not given, then default value is 'relation'
        """
        if not relation_name:
            relation_name = 'relation'
        if hasattr(self.modelb, relation_name):
            raise Error("The attribute name %s has already existed in Model %s!" % (relation_name, self.modelb.__name__))
        if not self.through_model:
            raise Error("Only with through style in ManyToMany supports with_relation function of Model %s!" % self.modelb.__name__)
        self.with_relation_name = relation_name
        return self
        
    def run(self, limit=0):
        query = self.get_query()
        if limit > 0:
            query = getattr(query, 'limit')(limit)
        self.result = self.do_(query)
        return self.result
        
    def get_query(self):
        #user can define default_query, and default_query 
        #should be class method
        if self.default_query_flag:
            _f = getattr(self.modelb, 'default_query', None)
            if _f:
                _f(self)
        if self.with_relation_name:
            columns = list(self.table.c) + self.columns
        else:
            columns = self.columns
        query = select(
            self.get_columns(self.modelb, columns), 
            (self.table.c[self.fielda] == self.valuea) & 
            (self.table.c[self.fieldb] == self.modelb.c[self.realfieldb]) & 
            self.condition,
            **self.kwargs)
        for func, args, kwargs in self.funcs:
            query = getattr(query, func)(*args, **kwargs)
        if self._group_by:
            query = query.group_by(*self._group_by)
            if self._having:
                query = query.having(*self._having)
        return query
    
    def one(self):
        self.run(1)
        if not self.result:
            return
        result = self.result.fetchone()
        if result:
            if self._values_flag:
                return result

            offset = 0
            if self.with_relation_name:
                offset = len(self.table.columns)
                
            o = self.modelb.load(zip(result.keys()[offset:], result.values()[offset:]))
            
            if self.with_relation_name:
                r = self.through_model.load(zip(result.keys()[:offset], result.values()[:offset]))
                setattr(o, self.with_relation_name, r)
                
            return o

    def __del__(self):
        if self.result:
            self.result.close()
            self.result = None
    
    def __iter__(self):
        self.run()
        if not self.result:
            raise StopIteration

        offset = 0
        if self.with_relation_name:
            offset = len(self.table.columns)
        
        while 1:
            result = self.result.fetchone()
            if not result:
                raise StopIteration
            if self._values_flag:
                yield result
                continue
           
            o = self.modelb.load(zip(result.keys()[offset:], result.values()[offset:]))
            
            if self.with_relation_name:
                r = self.through_model.load(zip(result.keys()[:offset], result.values()[:offset]))
                setattr(o, self.with_relation_name, r)
                
            yield o
        
class ManyToMany(ReferenceProperty):
    type_name = 'ManyToMany'

    def __init__(self, reference_class=None, label=None, collection_name=None,
        reference_fieldname=None, reversed_fieldname=None, required=False, through=None, 
        through_reference_fieldname=None, through_reversed_fieldname=None, 
        **attrs):
        """
        Definition of ManyToMany property

        :param reference_fieldname: relative to field of B
        :param reversed_fieldname: relative to field of A
        :param through_reference_fieldname: through model relative to field of B
        :param through_reversed_fieldname: throught model relative to field of A
        :param index_reverse: create index reversed
        """
            
        super(ManyToMany, self).__init__(reference_class=reference_class,
            label=label, collection_name=collection_name,
            reference_fieldname=reference_fieldname, required=required, **attrs)
    
        self.reversed_fieldname = reversed_fieldname
        self.through = through

        self.through_reference_fieldname = through_reference_fieldname
        self.through_reversed_fieldname = through_reversed_fieldname
        self.index_reverse = attrs['index_reverse'] if 'index_reverse' in attrs else __manytomany_index_reverse__

    def create(self, cls):
        if not self.through:
            self.fielda = "%s_id" % self.model_class.tablename
            #test model_a is equels model_b
            #modified by limodou
            #if self.model_class.tablename == self.reference_class.tablename:
            if cls.tablename == self.reference_class.tablename:
                _t = self.reference_class.tablename + '_b'
            else:
                _t = self.reference_class.tablename
            self.fieldb = "%s_id" % _t
            self.table = self.create_table()
            #add appname to self.table
            # appname = self.model_class.__module__
            appname = cls.__module__
            self.table.__appname__ = appname[:appname.rfind('.')]
            #modified by limodou
            #self.model_class.manytomany.append(self.table)
            cls.manytomany.append(self.table)
            index_name = '%s_mindx' % self.tablename
            if index_name not in [x.name for x in self.table.indexes]:
                Index(index_name, self.table.c[self.fielda], self.table.c[self.fieldb], unique=True)
                #add field_b index
                if self.index_reverse:
                    Index('%s_rmindx' % self.tablename, self.table.c[self.fieldb])

            #process __mapping_only__ property, if the modela or modelb is mapping only
            #then manytomany table will be mapping only
            # if getattr(self.model_class, '__mapping_only__', False) or getattr(self.reference_class, '__mapping_only__', False):
            if getattr(cls, '__mapping_only__', False) or getattr(self.reference_class, '__mapping_only__', False):
                self.table.__mapping_only__ = True
            else:
                self.table.__mapping_only__ = False
    
    def get_real_property(self, model, field):
        return getattr(model, field).field_class
    
    def get_type(self, model, field):
        field = getattr(model, field)
        field_class = field.field_class
        if field.max_length:
            f_type = field_class(field.max_length)
        else:
            f_type = field_class
        return f_type
    
    def create_table(self):
        _table = Table(self.tablename, self.model_class.metadata,
            Column(self.fielda, self.get_type(self.model_class, self.reversed_fieldname)),
            Column(self.fieldb, self.get_type(self.reference_class, self.reference_fieldname)),
#            ForeignKeyConstraint([a], [a_id]),
#            ForeignKeyConstraint([b], [b_id]),
            extend_existing=True
        )
        return _table
    
    def init_through(self):
        def find_property(properties, model, skip=None):
            for k, v in properties.items():
                if isinstance(v, ReferenceProperty) and v.reference_class is model and (not skip or skip and v.reference_class is not skip):
                    return k, v

        if self.through and (not isinstance(self.through, type) or not issubclass(self.through, Model)):
            if not (
                    (isinstance(self.through, type) and issubclass(self.reference_class, Model)) or
                    valid_model(self.reference_class)):
                raise KindError('through must be Model or available table name')
            self.through = get_model(self.through, engine_name=self.engine_name,
                                                                 signal=False)
            #auto find model
            _auto_model = None
            #process through_reference_fieldname
            if self.through_reversed_fieldname:
                k = self.through_reversed_fieldname
                v = self.through.properties.get(k)
                if not v:
                    raise BadPropertyTypeError("Can't find property %s in through model %s" % (
                        k, self.through.__name__))
            else:
                x = find_property(self.through.properties, self.model_class)
                if not x:
                    raise BadPropertyTypeError("Can't find reference property of model %s in through model %s" % (
                        self.model_class.__name__, self.through.__name__))
                k, v = x
                _auto_model = self.model_class
            self.fielda = k
            self.reversed_fieldname = v.reference_fieldname

            #process through_reversed_fieldname
            if self.through_reference_fieldname:
                k = self.through_reference_fieldname
                v = self.through.properties.get(k)
                if not v:
                    raise BadPropertyTypeError("Can't find property %s in through model %s" % (
                        k, self.through.__name__))
            else:
                x = find_property(self.through.properties, self.reference_class, self.model_class)
                if not x:
                    raise BadPropertyTypeError("Can't find reference property of model %s in through model %s" % (
                        self.model_class.__name__, self.through.__name__))
                k, v = x
                #check if the auto find models are the same
                if _auto_model and _auto_model is self.reference_class:
                    raise BadPropertyTypeError("If the two reference fields come from the same"
                        " model, you should specify them via through_reference_fieldname or"
                        " through_reversed_fieldname in through model %s" % self.through.__name__)
            self.fieldb = k
            self.reference_fieldname = v.reference_fieldname

            self.table = self.through.table
            appname = self.model_class.__module__
            self.table.__appname__ = appname[:appname.rfind('.')]
            self.model_class.manytomany.append(self.table)
            Index('%s_mindx' % self.tablename, self.table.c[self.fielda], self.table.c[self.fieldb], unique=True)
    
    def __property_config__(self, model_class, property_name):
        """Loads all of the references that point to this model.
        """
        
        #Direct invoke super with ReferenceProperty in order to skip the
        #ReferenceProperty process, but instead of invode ReferenceProperty's
        #parent function
        super(ReferenceProperty, self).__property_config__(model_class, property_name)
    
        if not (
                (isinstance(self.reference_class, type) and issubclass(self.reference_class, Model)) or
                self.reference_class is _SELF_REFERENCE or
                valid_model(self.reference_class, self.engine_name)):
            raise KindError('reference_class %r must be Model or _SELF_REFERENCE or available table name' % self.reference_class)

        if self.reference_class is _SELF_REFERENCE or self.reference_class is None:
            self.reference_class = self.data_type = model_class
        else:
            self.reference_class = get_model(self.reference_class, self.engine_name,
                                             signal=False)
        self.reference_fieldname = self.reference_fieldname or self.reference_class._primary_field
        self.reversed_fieldname = self.reversed_fieldname or model_class._primary_field
        self.tablename = '%s_%s_%s' % (model_class.tablename, self.reference_class.tablename, property_name)
        self.collection_name = self.reference_class.get_collection_name(model_class.tablename, self._collection_name, model_class.tablename)
        setattr(self.reference_class, self.collection_name,
            _ManyToManyReverseReferenceProperty(self, self.collection_name))
    
    def get_lazy(self, model_instance, name, default=None):
        v = self.get_attr(model_instance, name, default)
        if v is Lazy:
#            _id = getattr(model_instance, 'id')
#            if not _id:
#                raise BadValueError('Instance is not a validate object of Model %s, ID property is not found' % model_instance.__class__.__name__)
            result = getattr(model_instance, self.name)
            v = result.keys(True)
            setattr(model_instance, name, v)
            
            #2014/3/1 save value to Model_instance._old_values
            #this will cause manytomany need not to check when saving
            #or it'll compare the difference between old_value and database(use select)
            model_instance._old_values[self.name] = v
        return v

    def __get__(self, model_instance, model_class):
        """Get reference object.
    
        This method will fetch unresolved entities from the datastore if
        they are not already loaded.
    
        Returns:
            ReferenceProperty to Model object if property is set, else None.
        """
        self.init_through()
        if model_instance:
            reference_id = getattr(model_instance, self.reversed_fieldname, None)
            x = ManyResult(self.model_class, model_instance, self.property_name, self.reference_class, self.table,
                self.fielda, self.fieldb, self.reversed_fieldname,
                self.reference_fieldname, reference_id, through_model=self.through)
            return x
        else:
            return self
    
    def __set__(self, model_instance, value):
        if model_instance is None:
            return
        
        if value and value is not Lazy:
            value = get_objs_columns(value, self.reference_fieldname, model=self.reference_class)
        setattr(model_instance, self._attr_name(), value)
    
    def get_value_for_datastore(self, model_instance, cached=False):
        """Get key of reference rather than reference itself."""
        value = getattr(model_instance, self._attr_name(), None)
        if not cached:
            value = getattr(model_instance, self.property_name).keys()
            setattr(model_instance, self._attr_name(), value)
        return value
    
    def get_display_value(self, value):
        s = []
        for x in value:
            s.append(unicode(x))
        return ' '.join(s)
    
    def in_(self, *objs):
        """
        Create a condition
        """
        if not objs:
            return self.table.c[self.fielda]!=self.table.c[self.fielda]
        else:
            keys = get_objs_columns(objs, self.reference_fieldname)
            sub_query = select([self.table.c[self.fielda]], (self.table.c[self.fieldb] == self.reference_class.c[self.reference_fieldname]) & (self.table.c[self.fieldb].in_(keys)))
            condition = self.model_class.c[self.reversed_fieldname].in_(sub_query)
            return condition
         
    def join_in(self, *objs):
        """
        Create a join condition, connect A and C
        """
        if not objs:
            return self.table.c[self.fielda]!=self.table.c[self.fielda]
        else:
            keys = get_objs_columns(objs, self.reference_fieldname)
            return (self.table.c[self.fielda] == self.model_class.c[self.reversed_fieldname]) & (self.table.c[self.fieldb].in_(keys))
   
    def join_right_in(self, *objs):
        """
        Create a join condition, connect B and C
        """
        if not objs:
            return self.table.c[self.fielda]!=self.table.c[self.fielda]
        else:
            keys = get_objs_columns(objs, self.reference_fieldname)
            return (self.table.c[self.fieldb] == self.reference_class.c[self.reference_fieldname]) & (self.table.c[self.fielda].in_(keys))
    
    def filter(self, *condition):
        cond = true()
        for c in condition:
            if c is not None:
                cond = and_(c, cond)
        sub_query = select([self.table.c[self.fielda]], (self.table.c[self.fieldb] == self.reference_class.c[self.reference_fieldname]) & cond)
        condition = self.model_class.c[self.reversed_fieldname].in_(sub_query)
        return condition

    def join_filter(self, *condition):
        cond = true()
        for c in condition:
            if c is not None:
                cond = and_(c, cond)
        return (self.table.c[self.fielda] == self.model_class.c[self.reversed_fieldname]) & (self.table.c[self.fieldb] == self.reference_class.c[self.reference_fieldname]) & cond
        
    def convert_dump(self, value):
        if not value:
            return []
        return [int(x) for x in value.split(',')]

    def to_column_info(self):
        d = {}
        d['verbose_name'] = self.verbose_name or ''
        d['label'] = self.label or ''
        d['name'] = self.name
        d['fieldname'] = self.fieldname
        d['type'] = self.type_name
        d['type_name'] = self.type_name
        d['relation'] = 'ManyToMany(%s:%s-%s:%s)' % (self.model_class.__name__, self.reversed_fieldname,
            self.reference_class.__name__, self.reference_fieldname)
        self._get_column_info(d)
        return d

def SelfReferenceProperty(label=None, collection_name=None, **attrs):
    """Create a self reference.
    """
    if 'reference_class' in attrs:
        raise ConfigurationError(
                'Do not provide reference_class to self-reference.')
    return ReferenceProperty(_SELF_REFERENCE, label, collection_name, **attrs)

SelfReference = SelfReferenceProperty

class _ReverseReferenceProperty(Property):
    """The inverse of the Reference property above.

    We construct reverse references automatically for the model to which
    the Reference property is pointing to create the one-to-many property for
    that model.    For example, if you put a Reference property in model A that
    refers to model B, we automatically create a _ReverseReference property in
    B called a_set that can fetch all of the model A instances that refer to
    that instance of model B.
    """

    def __init__(self, model, reference_id, reversed_id):
        """Constructor for reverse reference.

        Constructor does not take standard values of other property types.

        """
        self._model = model                 #A
        self._reference_id = reference_id   #A Reference(B) this is A's reference field
        self._reversed_id = reversed_id     #B's reference_field
        self.verbose_name = ''
        self.label = ''

    def __get__(self, model_instance, model_class):
        """Fetches collection of model instances of this collection property."""
        if model_instance is not None:      #model_instance is B's
            _id = getattr(model_instance, self._reversed_id, None)
            if _id is not None:
                a_id = self._reference_id
                a_field = self._model.c[self._reference_id]
                return ReverseResult(self._model, a_field==_id, self._reference_id, model_class.table, model_instance, self._reversed_id)
            else:
#                return Result()
                return None
        else:
            return self

    def __set__(self, model_instance, value):
        """Not possible to set a new collection."""
        raise BadValueError('Virtual property is read-only')

class _OneToOneReverseReferenceProperty(_ReverseReferenceProperty):
    def __init__(self, model, reference_id, reversed_id, collection_name):
        """Constructor for reverse reference.
    
        Constructor does not take standard values of other property types.
    
        """
        self._model = model
        self._reference_id = reference_id    #B Reference(A) this is B's id
        self._reversed_id = reversed_id    #A's id
        self._collection_name = collection_name

    def __get__(self, model_instance, model_class):
        """Fetches collection of model instances of this collection property."""
        if model_instance:
            _id = getattr(model_instance, self._reversed_id, None)

            # print self._resolved_attr_name()
            if _id is not None:
                #this will cache the reference object
                resolved = getattr(model_instance, self._resolved_attr_name(), None)
                if resolved is not None:
                    return resolved
                else:
                    b_id = self._reference_id
                    d = self._model.c[self._reference_id]
                    instance = self._model.get(d==_id)
                    if not instance:
                        instance = self._model(**{b_id:_id})
                        instance.save()
                    setattr(model_instance, self._resolved_attr_name(), instance)
                    return instance

            else:
                return None
        else:
            return self

    def _resolved_attr_name(self):
        """Get attribute of resolved attribute.

        The resolved attribute is where the actual loaded reference instance is
        stored on the referring model instance.

        Returns:
            Attribute name of where to store resolved reference model instance.
        """
        return '_RESOLVED_' + self._collection_name

class _ManyToManyReverseReferenceProperty(_ReverseReferenceProperty):
    def __init__(self, reference_property, collection_name):
        """Constructor for reverse reference.
    
        Constructor does not take standard values of other property types.
    
        """
        self.reference_property = reference_property
        self._collection_name = collection_name

    def __get__(self, model_instance, model_class):
        """Fetches collection of model instances of this collection property."""
        self.reference_property.init_through()
        self._reversed_id = self.reference_property.reference_fieldname
        if model_instance:
            reference_id = getattr(model_instance, self._reversed_id, None)
            x = ManyResult(self.reference_property.reference_class, model_instance,
                self._collection_name,
                self.reference_property.model_class, self.reference_property.table,
                self.reference_property.fieldb, self.reference_property.fielda, 
                self.reference_property.reference_fieldname,
                self.reference_property.reversed_fieldname, reference_id, 
                through_model=self.reference_property.through)
            return x
        else:
            return self


FILE = FileProperty
PICKLE = PickleProperty
UUID = UUIDProperty
UUID_B = UUIDBinaryProperty
JSON = JsonProperty

_fields_mapping = {
    'bigint':BigIntegerProperty,
    BIGINT:BigIntegerProperty,
    str:StringProperty,
    'varchar':StringProperty,
    VARCHAR:StringProperty,
    'char':CharProperty,
    CHAR:CharProperty,
    unicode: UnicodeProperty,
    'binary': BinaryProperty,
    BINARY: BinaryProperty,
    'varbinary': VarBinaryProperty,
    VARBINARY: VarBinaryProperty,
    'text': TextProperty,
    TEXT: TextProperty,
    'blob': BlobProperty,
    BLOB: BlobProperty,
    int:IntegerProperty,
    'smallint': SmallIntegerProperty,
    SMALLINT: SmallIntegerProperty,
    INT:IntegerProperty,
    float:FloatProperty,
    FLOAT:FloatProperty,
    bool:BooleanProperty,
    BOOLEAN:BooleanProperty,
    'datetime':DateTimeProperty,
    datetime.datetime:DateTimeProperty,
    DATETIME:DateTimeProperty,
    'json':JsonProperty,
    JSON:JsonProperty,
    datetime.date:DateProperty,
    'date':DateProperty,
    DATE:DateProperty,
    datetime.time:TimeProperty,
    'time':TimeProperty,
    TIME:TimeProperty,
    'decimal':DecimalProperty,
    decimal.Decimal:DecimalProperty,
    DECIMAL:DecimalProperty,
    UUID_B:UUIDBinaryProperty,
    'uuid':UUIDProperty,
    UUID:UUIDProperty
}
def Field(type, *args, **kwargs):
    t = _fields_mapping.get(type, type)
    return t(*args, **kwargs)

def get_field_type(_type):
    assert isinstance(_type, (str, unicode))

    t = _fields_mapping.get(_type)
    if not t:
        _t = eval(_type)
        t = _fields_mapping.get(_t, _t)
    return t

def get_model_property(model, name):
    if '.' not in name:
        prop = get_model(model).properties.get(name)
    else:
        _name, _field = name.split('.')
        _model = get_model(_name)
        prop = _model.properties.get(_field)
    return prop

class ModelReprDescriptor(object):
    def __get__(self, model_instance, model_class):
        def f():
            from IPython.display import display_html, display_svg

            if model_instance is None:
                display_html(self._cls_repr_html_(model_class))
                display_svg(self._cls_repr_svg_(model_class))
            else:
                display_html(self._instance_repr_html_(model_instance))
        return f

    def _cls_repr_html_(self, cls):
        from IPython.display import HTML

        return HTML('<pre>'+print_model(cls)+'</pre>')

    def _cls_repr_svg_(self, cls):
        import os
        from uliweb.orm.graph import generate_file
        from uliweb import application
        from uliweb.utils.common import get_tempfilename
        from IPython.display import SVG

        engine_name = cls.get_engine_name()
        fontname = os.environ.get('dot_fontname', '')
        outputfile = get_tempfilename('dot_svg_', suffix='.svg')
        generate_file({cls.tablename:cls.table}, application.apps,
                             outputfile, 'svg', engine_name, fontname=fontname)
        return SVG(filename=outputfile)

    def _instance_repr_html_(self, instance):
        from uliweb.core.html import Table
        from IPython.display import HTML

        s = []
        for k, v in instance._fields_list:
            if not isinstance(v, ManyToMany):
                info = v.to_column_info()
                d = [info['label'], info['name'], info['type_name']]
                t = getattr(instance, k, None)
                if isinstance(v, Reference) and t:
                    d.append('%s:%r:%s' % (v.reference_class.__name__, t._key, unicode(t)))
                else:
                    d.append(t)
                s.append(d)
        return HTML(str(Table(s, ['Display Name', 'Column Name',
                                          'Column Type', 'Value'])))

class Model(object):

    __metaclass__ = ModelMetaclass
    __dispatch_enabled__ = True
    _engine_name = None
    _connection = None
    _alias = None #can be used via get_model(alias)
    _collection_set_id = 1
    _bind = True
    _bound_classname = ''
    _base_class = None
    _primary_field = None
    _key = None #primary key property
    
    _lock = threading.Lock()
    _c_lock = threading.Lock()

    #add support for IPython notebook display
    _ipython_display_ = ModelReprDescriptor()
    
    def __init__(self, **kwargs):
        self._old_values = {}
        self._load(kwargs, from_='')
        self._saved = False
        
    def set_saved(self):
        self._old_values = self.to_dict()
        for k, v in self.properties.items():
            if isinstance(v, ManyToMany):
                t = v.get_value_for_datastore(self, cached=True)
                if not t is Lazy:
                    self._old_values[k] = t
        self._saved = True
        
    def to_dict(self, fields=None, convert=True, manytomany=False):
        d = {}
        fields = fields or []
        for k, v in self.properties.items():
            if fields and not k in fields:
                continue
            if not isinstance(v, ManyToMany):
                if convert:
                    t = v.get_value_for_datastore(self)
                    d[k] = self.field_str(t)
                else:
                    t = getattr(self, k)
                    d[k] = t
            else:
                if manytomany:
                    d[k] = getattr(self, v._lazy_value(), [])
        return d
    
    def field_str(self, v, strict=False):
        if v is None:
            if strict:
                return ''
            return v
        if isinstance(v, datetime.datetime):
            return v.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(v, datetime.date):
            return v.strftime('%Y-%m-%d')
        elif isinstance(v, datetime.time):
            return v.strftime('%H:%M:%S')
        elif isinstance(v, decimal.Decimal):
            return str(v)
        elif isinstance(v, unicode):
            return v.encode(__default_encoding__)
        else:
            if strict:
                return str(v)
            return copy.deepcopy(v)
           
    def _get_data(self, fields=None, compare=True):
        """
        Get the changed property, it'll be used to save the object
        If compare is False, then it'll include all data not only changed property
        """
        fields = fields or []
        if self._key is None or self._key == '':
            d = {}
            for k, v in self.properties.items():
                #test fields
                if fields and k not in fields:
                    continue
#                if not isinstance(v, ManyToMany):
                if v.property_type == 'compound':
                    continue
                if not isinstance(v, ManyToMany):
                    x = v.get_value_for_datastore(self)
                    if isinstance(x, Model):
                        x = x._key
                    elif x is None or (k==self._primary_field and not x):
                        if isinstance(v, DateTimeProperty) and v.auto_now_add:
                            x = v.now()
                        elif (v.auto_add or (not v.auto and not v.auto_add)):
                            x = v.default_value()
                else:
                    x = v.get_value_for_datastore(self, cached=True)
                if x is not None and not x is Lazy:
                    d[k] = x
        else:
            d = {}
            d[self._primary_field] = self._key
            for k, v in self.properties.items():
                if fields and k not in fields:
                    continue
                if v.property_type == 'compound':
                    continue
                t = self._old_values.get(k, None)
                if not isinstance(v, ManyToMany):
                    x = v.get_value_for_datastore(self)
                    if isinstance(x, Model):
                        x = x._key
                else:
                    x = v.get_value_for_datastore(self, cached=True)
                if not x is Lazy:
                    if (compare and t != self.field_str(x)) or not compare:
                        d[k] = x
        
        return d
            
    def is_saved(self):
        return self._saved
    
    def update(self, **data):
        for k, v in data.items():
            if k in self.properties:
                if not isinstance(self.properties[k], ManyToMany):
                    x = self.properties[k].get_value_for_datastore(self)
                    if self.field_str(x) != self.field_str(v):
                        setattr(self, k, v)
                else:
                    setattr(self, k, v)
        return self
            
    def save(self, insert=False, changed=None, saved=None,
            send_dispatch=True, version=False, version_fieldname=None, 
            version_exception=True):
        """
        If insert=True, then it'll use insert() indead of update()
        
        changed will be callback function, only when the non manytomany properties
        are saved, the signature is:
            
            def changed(created, old_data, new_data, obj=None):
                if flag is true, then it means the record is changed
                you can change new_data, and the new_data will be saved to database
                
        version = Optimistic Concurrency Control
        version_fieldname default is 'version'
        if check_many, it'll auto check if manytomany value need to save, 
        only available in UPDATE
        """
        _saved = False
        created = False
        version_fieldname = version_fieldname or 'version'
        d = self._get_data()
        #fix when d is empty, orm will not insert record bug 2013/04/07
        if d or not self._saved or insert:
            _id = d.get(self._primary_field, None)
            if insert or not self._saved or not _id:
                created = True
                old = d.copy()
                
                if get_dispatch_send() and self.__dispatch_enabled__:
                    dispatch.call(self.__class__, 'pre_save', instance=self, created=True, data=d, old_data=self._old_values, signal=self.tablename)
                
                #process auto_now_add
                _manytomany = {}
                for k, v in self.properties.items():
                    if v.property_type == 'compound':
                        continue
                    if not isinstance(v, ManyToMany):
                        if isinstance(v, DateTimeProperty) and v.auto_now_add and k not in d:
                            d[k] = v.now()
                        elif (not k in d) and v.auto_add:
                            d[k] = v.default_value()
                    else:
                        if k in d:
                            _manytomany[k] = d.pop(k)
                if d:
                    if callable(changed):
                        changed(self, created, self._old_values, d)
                        old.update(d)
                    obj = do_(self.table.insert().values(**d), self.get_session())
                    _saved = True

                    if obj.inserted_primary_key and self._primary_field:
                        setattr(self, self._primary_field, obj.inserted_primary_key[0])

                if _manytomany:
                    for k, v in _manytomany.items():
                        if v:
                            _saved = getattr(self, k).update(v) or _saved
                
            else:
                _id = d.pop(self._primary_field)
                if d:
                    old = d.copy()
                    if get_dispatch_send() and self.__dispatch_enabled__:
                        dispatch.call(self.__class__, 'pre_save', instance=self, created=False, data=d, old_data=self._old_values, signal=self.tablename)

                    #process auto_now
                    _manytomany = {}
                    for k, v in self.properties.items():
                        if v.property_type == 'compound' or k == self._primary_field:
                            continue
                        if not isinstance(v, ManyToMany):
                            if isinstance(v, DateTimeProperty) and v.auto_now and k not in d:
                                d[k] = v.now()
                            elif (not k in d) and v.auto:
                                d[k] = v.default_value()
                        else:
                            if k in d:
                                _manytomany[k] = d.pop(k)
                    if d:
                        _cond = self.table.c[self._primary_field] == self._key
                        if version:
                            version_field = self.table.c.get(version_fieldname)
                            if version_field is None:
                                raise KindError("version_fieldname %s is not existed in Model %s" % (version_fieldname, self.__class__.__name__))
                            _version_value = getattr(self, version_fieldname, 0)
                            # setattr(self, version_fieldname, _version_value+1)
                            d[version_fieldname] = _version_value+1
                            _cond = (version_field == _version_value) & _cond
                            
                        if callable(changed):
                            changed(self, created, self._old_values, d)
                            old.update(d)
                        result = do_(self.table.update(_cond).values(**d), self.get_session())
                        _saved = True
                        if version:
                            if result.rowcount == 0:
                                _saved = False
                                if version_exception:
                                    raise SaveError("The record {0}:{1} has been saved by others, current version is {2}".format(
                                        self.tablename, self._key, _version_value))
                            else:
                                setattr(self, version_fieldname, d[version_fieldname])
                        elif result.rowcount == 0:
                            _saved = False
                            # raise NotFound("The record can't be found!", self.tablename, self._key)
                      
                    if _manytomany:
                        for k, v in _manytomany.items():
                            if v is not None:
                                _saved = getattr(self, k).update(v) or _saved

                # else:
                #     #check if the field is primary_key, true will raise Exception
                #     #2015/11/20 limodou
                #     raise ValueError("You can't only change primary key '{}'.".format(self._primary_field))


            if _saved:
                for k, v in d.items():
                    x = self.properties[k].get_value_for_datastore(self)
                    if self.field_str(x) != self.field_str(v):
                        setattr(self, k, v)
                if send_dispatch and get_dispatch_send() and self.__dispatch_enabled__:
                    dispatch.call(self.__class__, 'post_save', instance=self, created=created, data=old, old_data=self._old_values, signal=self.tablename)
                self.set_saved()
                
                if callable(saved):
                    saved(self, created, self._old_values, old)

        return _saved

    def put(self, *args, **kwargs):
        warnings.simplefilter('default')
        warnings.warn("put method will be deprecated in next version.", DeprecationWarning)
        return self.save(*args, **kwargs)

    def delete(self, manytomany=True, delete_fieldname=None, send_dispatch=True,
               onetoone=True):
        """
        Delete current obj
        :param manytomany: if also delete all manytomany relationships
        :param delete_fieldname: if True then it'll use 'deleted', others will 
        be the property name
        """
        if get_dispatch_send() and self.__dispatch_enabled__:
            dispatch.call(self.__class__, 'pre_delete', instance=self, signal=self.tablename)
        if manytomany:
            for k, v in self._manytomany.items():
                getattr(self, k).clear()
        if onetoone:
            for k, v in self._onetoone.items():
                row = getattr(self, k)
                if row:
                    row.delete()
        if delete_fieldname:
            if delete_fieldname is True:
                delete_fieldname = 'deleted'
            if not hasattr(self, delete_fieldname):
                raise KeyError("There is no %s property exists" % delete_fieldname)
            setattr(self, delete_fieldname, True)
            self.save()
        else:
            do_(self.table.delete(self.table.c[self._primary_field]==self._key), self.get_session())
            self._key = None
            self._old_values = {}
        if send_dispatch and get_dispatch_send() and self.__dispatch_enabled__:
            dispatch.call(self.__class__, 'post_delete', instance=self, signal=self.tablename)

    def create_sql(self, insert=False, version=False, version_fieldname=None,
                   fields=None, ec=None, compare=False):
        """
        Create sql statement, do not process manytomany
        """
        version_fieldname = version_fieldname or 'version'
        #fix when d is empty, orm will not insert record bug 2013/04/07
        if not self._key or insert:
            d = self._get_data(fields, compare=compare)
            if d:
                return rawsql(self.table.insert().values(**d),
                              ec or self.get_engine_name()) + ';'

        else:
            d = self._get_data(fields, compare=compare)
            _key = d.pop(self._primary_field)
            if d:
                _cond = self.table.c[self._primary_field] == self._key
                if version:
                    version_field = self.table.c.get(version_fieldname)
                    if version_field is None:
                        raise KindError("version_fieldname %s is not existed in Model %s" % (version_fieldname, self.__class__.__name__))
                    _version_value = getattr(self, version_fieldname, 0)
                    # setattr(self, version_fieldname, _version_value+1)
                    d[version_fieldname] = _version_value+1
                    _cond = (version_field == _version_value) & _cond

                return rawsql(self.table.update(_cond).values(**d),
                              ec or self.get_engine_name()) + ';'
        return ''

    def __repr__(self):
        s = []
        for k, v in self._fields_list:
            if not isinstance(v, ManyToMany):
                t = getattr(self, k, None)
                if isinstance(v, Reference) and t:
                    s.append('{0!r}:<{1}:{2}>'.format(k, v.__class__.__name__, t._key))
                else:
                    s.append('%r:%r' % (k, t))
        if self.__class__._base_class:
            clsname = self.__class__._base_class.__name__
        else:
            clsname = self.__class__.__name__
        return ('<%s {' % clsname) + ','.join(s) + '}>'
    
    def __str__(self):
        return str(self._key)
    
    def __unicode__(self):
        return str(self._key)

    def get_display_value(self, field_name, value=None):
        return self.properties[field_name].get_display_value(value or getattr(self, field_name))
        
    def get_datastore_value(self, field_name):
        return self.properties[field_name].get_value_for_datastore(self)

    #classmethod========================================================

    @classmethod
    def add_property(cls, name, prop, config=True, set_property=True):
        if isinstance(prop, Property):
            check_reserved_word(name)
            #process if there is already the same property
            old_prop = cls.properties.get(name)
            if old_prop:
                prop.creation_counter = old_prop.creation_counter
            cls.properties[name] = prop
            if config:
                prop.__property_config__(cls, name)
            if set_property:
                setattr(cls, name, prop)
            if hasattr(cls, '_fields_list'):
                index = -1
                for i, (n, p) in enumerate(cls._fields_list):
                    if name == n:
                        index = i
                        break
                   
                if index >= 0:
                    cls._fields_list[index] = (name, prop)
                else:
                    cls._fields_list.append((name, prop))
                    cls._fields_list.sort(lambda x, y: cmp(x[1].creation_counter, y[1].creation_counter))
        else:
            raise AttributeError("Prop should be instance of Property, but %r found" % prop)

    @classmethod
    def update_property(cls, name, prop, config=True, set_property=True):
        if isinstance(prop, Property):
            old_prop = cls.properties[name]
            prop.creation_counter = old_prop.creation_counter
            cls.properties[name] = prop
            if config:
                prop.__property_config__(cls, name)
            if set_property:
                setattr(cls, name, prop)
            if hasattr(cls, '_fields_list'):
                index = -1
                for i, (n, p) in enumerate(cls._fields_list):
                    if name == n:
                        index = i
                        break
                    
                if index >= 0:
                    cls._fields_list[index] = (name, prop)
        else:
            raise AttributeError("Prop should be instance of Property, but %r found" % prop)
        
    @classmethod
    def get_collection_name(cls, from_class_name, collection_name=None, prefix=None):
        """
        Get reference collection_name, if the collection_name is None
        then make sure the collection_name is not conflict, but
        if the collection_name is not None, then check if the collection_name
        is already exists, if existed then raise Exception.
        """
        if not collection_name:
            collection_name = prefix + '_set'
            if hasattr(cls, collection_name):
                #if the xxx_set is already existed, then automatically
                #create unique collection_set id
                collection_name = prefix + '_set_' + str(cls._collection_set_id)
                cls._collection_set_id += 1
        else:
            if collection_name in cls._collection_names:
                if cls._collection_names.get(collection_name) != from_class_name:
                    raise DuplicatePropertyError("Model %s already has property %s" % (cls.__name__, collection_name))
        return collection_name
            
    @classmethod
    def Reference(cls, name, model, reference_fieldname=None, collection_name=None, **kwargs):
        field_from = getattr(cls, name)
        if not field_from:
            raise AttributeError("Field %s can't be found in Model %s" % (name, cls.tablename))
        d = field_from.get_parameters()
        d.update(kwargs)
        prop = ReferenceProperty(reference_class=model, 
            reference_fieldname=reference_fieldname,
            collection_name=collection_name,
            **d)

        cls.update_property(name, prop)
        
    @classmethod
    def OneToOne(cls, name, model, reference_fieldname=None, collection_name=None, **kwargs):
        field_from = getattr(cls, name)
        if not field_from:
            raise AttributeError("Field %s can't be found in Model %s" % (name, cls.tablename))
        d = field_from.get_parameters()
        d.update(kwargs)
        prop = OneToOne(reference_class=model, 
            reference_fieldname=reference_fieldname,
            collection_name=collection_name,
            **d)
        
        cls.update_property(name, prop)
        
    @classmethod
    def ManyToMany(cls, name, model, collection_name=None, 
        reference_fieldname=None, reversed_fieldname=None, required=False, 
        through=None, 
        through_reference_fieldname=None, through_reversed_fieldname=None, 
        **kwargs):
        prop = ManyToMany(reference_class=model, 
            collection_name=collection_name,
            reference_fieldname=reference_fieldname,
            reversed_fieldname=reversed_fieldname,
            through=through,
            through_reference_fieldname=through_reference_fieldname,
            through_reversed_fieldname=through_reversed_fieldname,
            **kwargs)
        cls.add_property(name, prop)
        #create property, it'll create Table object
        prop.create(cls)
        #create real table
        if __auto_create__:
            engine = cls.get_engine().engine
            if not prop.through and not prop.table.exists(engine):
                prop.table.create(engine, checkfirst=True)

    @classmethod
    def _set_tablename(cls, appname=None):
        if not hasattr(cls, '__tablename__'):
            name = get_tablename(cls.__name__)
        else:
            name = cls.__tablename__
        if appname:
            name = appname.lower() + '_' + name
        cls.tablename = name
        
    @classmethod
    def get_session(cls):
        if cls._connection:
            return cls._connection
        return get_session(cls.get_engine_name())
        
    @classmethod
    def get_engine_name(cls):
        return cls._engine_name or __default_engine__
    
    @classmethod
    def get_engine(cls):
        ec = cls.get_engine_name()
        return engine_manager[ec]
        
    @classmethod
    def _use(cls, ec):
        """
        underly implement of use
        """
        # class ConnectModel(cls):
        #     pass
        ConnectModel = type(cls.__name__, (cls,), {})

        ConnectModel.tablename = cls.tablename
        ConnectModel._base_class = cls
        if isinstance(ec, (str, unicode)):
            ConnectModel._engine_name = ec
        elif isinstance(ec, Session):
            ConnectModel._engine_name = ec.engine_name
            ConnectModel._connection = ec
        return ConnectModel
    
    @classmethod
    def use(cls, ec):
        """
        use will duplicate a new Model class and bind ec
        
        ec is Engine name or Sesstion object
        """
        
        if isinstance(ec, (str, unicode)):
            m = get_model(cls._alias, ec, signal=False)
        else:
            m = cls._use(ec)
        return m
    
    @classmethod
    def bind(cls, metadata=None, auto_create=False, reset=False):
        cls._lock.acquire()
        try:
            cls.metadata = metadata or find_metadata(cls)
            if cls.metadata:
                cols = []
                cls.manytomany = []
                #add pre_create process
                for k, f in cls._fields_list:
                    func = getattr(f, 'pre_create', None)
                    if func:
                        func(cls)

                #add auto_create support for testing 2015.10.29
                if not __lazy_model_init__:
                    for k, v in cls.properties.items():
                        v.__property_config__(cls, k)

                for k, f in cls._fields_list:
                    c = f.create(cls)
                    if c is not None:
                        cols.append(c)

                if not getattr(cls, '__dynamic__', False):
                    #check the model_path
                    if cls._base_class:
                        model_path = cls._base_class.__module__ + '.' + cls._base_class.__name__
                    else:
                        model_path = cls.__module__ + '.' + cls.__name__
                    _path = __models__.get(cls.tablename, {}).get('model_path', '')
                    if _path and model_path != _path:
                        return
                
                #check if the table is already existed
                t = cls.metadata.tables.get(cls.tablename, None)
                if t is not None and not __auto_set_model__ and not reset:
                    return 
                
                if t is not None:
                    cls.metadata.remove(t)
                args = getattr(cls, '__table_args__', {})
                args['mysql_charset'] = 'utf8'
                cls.table = Table(cls.tablename, cls.metadata, *cols, **args)
                #add appname to self.table
                appname = cls.__module__
                cls.table.__appname__ = appname[:appname.rfind('.')]
                
                #add __mapping_only__ property to Table object
                cls.table.__mapping_only__ = getattr(cls, '__mapping_only__', False)
                
                cls.c = cls.table.c
                cls.columns = cls.table.c
                
                if hasattr(cls, 'OnInit'):
                    cls.OnInit()
                
                if auto_create:
                    #only metadata is and bound 
                    #then the table will be created
                    #otherwise the creation of tables will be via: create_all(db)
                    if cls.metadata.bind:
                        cls.create()
                        set_model(cls, created=True)
                    else:
                        set_model(cls)
                else:
                    if __auto_set_model__:
                        set_model(cls)
                        
                cls._bound_classname = cls._alias
        finally:
            cls._lock.release()
            
    @classmethod
    def create(cls):
        cls._c_lock.acquire()
        try:
            engine = get_connection(cls.get_engine_name())
            if not cls.table.exists(engine):
                cls.table.create(engine, checkfirst=True)
            for x in cls.manytomany:
                if not x.exists(engine):
                    x.create(engine, checkfirst=True)
        finally:
            cls._c_lock.release()
            
    @classmethod
    def get(cls, id=None, condition=None, fields=None, cache=False, engine_name=None, **kwargs):
        """
        Get object from Model, if given fields, then only fields will be loaded
        into object, other properties will be Lazy
        
        if cache is True or defined __cacheable__=True in Model class, it'll use cache first
        """
        
        if id is None and condition is None:
            return None
        
        can_cacheable = (cache or getattr(cls, '__cacheable__', None)) and \
            isinstance(id, (int, long, str, unicode))
        if can_cacheable:
            #send 'get_object' topic to get cached object
            obj = dispatch.get(cls, 'get_object', id)
            if obj:
                return obj

        if condition is not None:
            _cond = condition
        else:
            if isinstance(id, ColumnElement):
                _cond = id
            else:
                _cond = cls.c[cls._primary_field] == id
            #todo
            # if isinstance(id, (int, long)):
            #     _cond = cls.c.id==id
            # elif isinstance(id, (str, unicode)) and id.isdigit():
            #     _cond = cls.c.id==int(id)
            # else:
            #     _cond = id

        #if there is no cached object, then just fetch from database
        obj = cls.filter(_cond, **kwargs).fields(*(fields or [])).one()
        
        if obj and cache or getattr(cls, '__cacheable__', None):
            dispatch.call(cls, 'set_object', instance=obj)

        return obj
    
    def put_cached(self):
        dispatch.call(self.__class__, 'set_object', instance=self)
    
    @classmethod
    def get_or_notfound(cls, condition=None, fields=None):
        obj = cls.get(condition, fields=fields)
        if not obj:
            raise NotFound("Can't found the object", cls, condition)
        return obj
    
    @classmethod
    def _data_prepare(cls, record):
        d = {}
        for k, v in record:
            p = cls.properties.get(k)
            if p and not isinstance(p, ManyToMany):
                d[str(k)] = p.make_value_from_datastore(v)
            else:
                d[str(k)] = v
        return d
    
    @classmethod
    def all(cls, **kwargs):
        return Result(cls, **kwargs)
        
    @classmethod
    def empty(cls, **kwargs):
        return Result(cls, **kwargs).filter(false())

    @classmethod
    def filter(cls, *condition, **kwargs):
        return Result(cls, **kwargs).filter(*condition)
            
    @classonlymethod
    def remove(cls, condition=None, **kwargs):
        if isinstance(condition, (tuple, list)):
            condition = cls.c[cls._primary_field].in_(condition)
        elif condition is not None and not isinstance(condition, ColumnElement):
            condition = cls.c[cls._primary_field]==condition
        #todo
        do_(cls.table.delete(condition, **kwargs), cls.get_session())
            
    @classmethod
    def count(cls, condition=None, **kwargs):
        count = do_(cls.table.count(condition, **kwargs), cls.get_session()).scalar()
        return count
    
    @classmethod
    def any(cls, *condition, **kwargs):
        return Result(cls, **kwargs).filter(*condition).any()
    
    @classmethod
    def load(cls, values, from_='db'):
        if isinstance(values, (list, tuple)):
            d = cls._data_prepare(values)
        elif isinstance(values, dict):
            d = values
        else:
            raise BadValueError("Can't support the data type %r" % values)
        
        o = cls()
        o._load(d, use_delay=True, from_=from_)
        o.set_saved()
            
        return o
    
    def refresh(self, fields=None, **kwargs):
        """
        Re get the instance of current id
        """
        cond = self.c[self._primary_field]==self._key
        query = self.filter(cond, **kwargs)
        if not fields:
            fields = list(self.table.c)
        
        v = query.values_one(*fields)
        if not v:
            raise NotFound('Instance <{0}:{1}> can not be found'.format(self.tablename, self._key))
        
        d = self._data_prepare(v.items())
        self.update(**d)
        self.set_saved()
        
    def _load(self, data, use_delay=False, from_='db'):
        if not data:
            return
        
        #compounds fields will be processed in the end
        compounds = []
        for prop in self.properties.values():
            if from_ == 'db':
                name = prop.fieldname
            else:
                name = prop.name
            if name in data:
                if prop.property_type == 'compound':
                    compounds.append(prop)
                    continue
                value = data[name]
                if from_ == 'dump':
                    value = prop.convert_dump(value)
            else:
                if prop.property_type == 'compound':
                    continue
#                if use_delay or isinstance(prop, ManyToMany):
                if use_delay:
                    value = Lazy
                else:
                    if name != self._primary_field:
                        value = prop.default_value()
                    else:
                        value = None

            prop.__set__(self, value)

        for prop in compounds:
            if from_ == 'db':
                name = prop.fieldname
            else:
                name = prop.name
            if name in data:
                value = data[name]
                prop.__set__(self, value)

    def dump(self, fields=None, exclude=None):
        """
        Dump current object to dict, but the value is string
        for manytomany fields will not automatically be dumpped, only when
        they are given in fields parameter
        """
        exclude = exclude or []
        d = {}
        if fields and self._primary_field not in fields:
            fields = list(fields)
            fields.append(self._primary_field)
        for k, v in self.properties.items():
            if ((not fields) or (k in fields)) and (not exclude or (k not in exclude)):
                if not isinstance(v, ManyToMany):
                    t = v.get_value_for_datastore(self)
                    if t is Lazy:
                        self.refresh()
                        t = v.get_value_for_datastore(self)
                    if isinstance(t, Model):
                        t = t._key
                    d[k] = v.to_str(t)
                else:
                    if fields:
                       d[k] = ','.join([str(x) for x in getattr(self, v._lazy_value(), [])])
        if self._primary_field and d and self._primary_field not in d:
            d[self._primary_field] = str(self._key)
        return d
        
    @classmethod
    def migrate(cls, manytomany=True):
        tables = [cls.tablename]
        if manytomany:
            for x in cls.manytomany:
                tables.append(x.name)

        migrate_tables(tables, cls.get_engine_name())

    @classmethod
    def clear_relation(cls):
        """
        Clear relation properties for reference Model, such as OneToOne, Reference,
        ManyToMany
        """
        for k, v in cls.properties.items():
            if isinstance(v, ReferenceProperty):
                if hasattr(v, 'collection_name') and hasattr(v.reference_class, v.collection_name):
                    delattr(v.reference_class, v.collection_name)

                    if isinstance(v, OneToOne):
                        #append to reference_class._onetoone
                        del v.reference_class._onetoone[v.collection_name]

    @classmethod
    def get_columns_info(cls):
        for k, v in cls._fields_list:
            yield v.to_column_info()

class Bulk(object):
    """
    Used to create bulk update and insert according sql statement

    e.g.

        b = Bulk(transcation=False, size=10, engine_name=None)
        b.add(name, table.insert().values({'field':'field',...}))
        b.add(name, table.update().values({'field':'field',...}).where(condition))
        b.put(name, values)
        b.close()
    """
    def __init__(self, transcation=False, size=1, engine_name=None):
        self.transcation = transcation
        self.size = size
        self.engine_name= engine_name or __default_engine__
        if isinstance(self.engine_name, (str, unicode)):
            self.engine = engine_manager[self.engine_name].engine
        else:
            self.engine = engine_name

        self.sqles = {}

        if self.transcation:
            Begin(self.engine_name)

    def prepare(self, name, sql):
        try:
            x = sql.compile(dialect=self.engine.dialect)
            fields = []
            for i in x.positiontup:
                v = i.rsplit('_', 1)
                if len(v) > 1:
                    n, tail = v
                    if tail.isdigit():
                        if n in fields:
                            fields.append(i)
                        else:
                            fields.append(n)
                    else:
                        fields.append(i)
                else:
                    fields.append(i)
            self.sqles[name] = {'fields':fields, 'raw_sql':unicode(x), 'data':[]}
        except:
            if self.transcation:
                Rollback(self.engine_name)
            raise

    def get_sql(self, name):
        return self.sqles[name]['raw_sql']

    def do_(self, name, **values):
        try:
            sql = self.sqles[name]
            d = [values[x] for x in sql['fields']]
            return do_(sql['raw_sql'], args=d)
        except:
            if self.transcation:
                Rollback(self.engine_name)
            raise

    def put(self, name, **values):
        """
        Put data to cach, if reached size value, it'll execute at once.
        """
        try:
            sql = self.sqles[name]
            data = sql['data']
            d = [values[x] for x in sql['fields']]
            data.append(d)
            if self.size and len(data) >= self.size:
                do_(sql['raw_sql'], args=data)
                sql['data'] = []
        except:
            if self.transcation:
                Rollback(self.engine_name)
            raise

    def close(self):
        try:
            for name, d in self.sqles.items():
                if d['data']:
                    do_(d['raw_sql'], args=d['data'])

            if self.transcation:
                Commit(self.engine_name)
        except:
            if self.transcation:
                Rollback(self.engine_name)
            raise




