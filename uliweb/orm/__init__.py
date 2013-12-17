# This module is used for wrapping SqlAlchemy to a simple ORM
# Author: limodou <limodou@gmail.com>


__all__ = ['Field', 'get_connection', 'Model', 'do_',
    'set_debug_query', 'set_auto_create', 'set_auto_set_model', 
    'get_model', 'set_model', 'engine_manager', 'set_auto_dotransaction',
    'set_tablename_converter', 'set_check_max_length', 'set_post_do',
    'rawsql', 'Lazy', 'set_echo',
    'CHAR', 'BLOB', 'TEXT', 'DECIMAL', 'Index', 'datetime', 'decimal',
    'Begin', 'Commit', 'Rollback', 'Reset', 'ResetAll', 'CommitAll', 'RollbackAll',
    'PICKLE', 'BIGINT', 'set_pk_type', 'PKTYPE',
    'BlobProperty', 'BooleanProperty', 'DateProperty', 'DateTimeProperty',
    'TimeProperty', 'DecimalProperty', 'FloatProperty', 'SQLStorage',
    'IntegerProperty', 'Property', 'StringProperty', 'CharProperty',
    'TextProperty', 'UnicodeProperty', 'Reference', 'ReferenceProperty',
    'PickleProperty', 'BigIntegerProperty',
    'SelfReference', 'SelfReferenceProperty', 'OneToOne', 'ManyToMany',
    'ReservedWordError', 'BadValueError', 'DuplicatePropertyError', 
    'ModelInstanceError', 'KindError', 'ConfigurationError',
    'BadPropertyTypeError', 'FILE', 'Begin', 'Commit', 'Rollback',
    'CommitAll', 'RollbackAll', 'set_lazy_model_init',
    'begin_sql_monitor', 'close_sql_monitor', 'set_model_config', 'text',
    'get_object', 'set_server_default', 'set_nullable', 'set_manytomany_index_reverse',
    ]

__auto_create__ = False
__auto_set_model__ = True
__auto_dotransaction__ = False
__debug_query__ = None
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
from uliweb.utils import date as _date
from uliweb.utils.common import flat_list, classonlymethod
from sqlalchemy import *
from sqlalchemy.sql import select, ColumnElement, text
from sqlalchemy.pool import NullPool
import sqlalchemy.engine.base as EngineBase
from uliweb.core import dispatch
import threading
from uliweb.utils.sorteddict import SortedDict

Local = threading.local()
Local.dispatch_send = True
Local.conn = {}
Local.trans = {}
Local.echo = False
Local.echo_func = sys.stdout.write

class Error(Exception):pass
class NotFound(Error):
    def __init__(self, message, model, id):
        self.message = message
        self.model = model
        self.id = id
        
    def __str__(self):
        return "%s(%s) instance can't be found" % (self.model.__name__, str(self.id))
class ReservedWordError(Error):pass
class ModelInstanceError(Error):pass
class DuplicatePropertyError(Error):
  """Raised when a property is duplicated in a model definition."""
class BadValueError(Error):pass
class BadPropertyTypeError(Error):pass
class KindError(Error):pass
class ConfigurationError(Error):pass

_SELF_REFERENCE = object()
class Lazy(object): pass

class SQLStorage(dict):
    """
    a dictionary that let you do d['a'] as well as d.a
    """
    def __getattr__(self, key): return self[key]
    def __setattr__(self, key, value):
        if self.has_key(key):
            raise SyntaxError, 'Object exists and cannot be redefined'
        self[key] = value
    def __repr__(self): return '<SQLStorage ' + dict.__repr__(self) + '>'

def set_auto_create(flag):
    global __auto_create__
    __auto_create__ = flag
    
def set_auto_dotransaction(flag):
    global __auto_dotransaction__
    __auto_dotransaction__ = flag

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

def set_echo(flag, time=None, explain=False, caller=True, out=sys.stdout.write):
    global Local
    
    Local.echo = flag
    Local.echo_func = out
    Local.echo_args = {'time':time, 'explain':explain, 'caller':caller}
    
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
    
class Transaction(object):
    def __init__(self, connection):
        self.connection = connection
        self.trans = connection.begin()
        
    def do_(self, query):
        return self.connection.execute(query)

    def __enter__(self):
        return self.do_
    
    def __exit__(self, type, value, tb):
        if self.trans:
            if type:
                self.trans.rollback()
            else:
                self.trans.commit()

class NamedEngine(object):
    def __init__(self, name, options):
        self.name = name
        
        d = SQLStorage({
            'engine_name':name,
            'connection_args':{},
            'debug_log':None,
            'connection_type':'long',
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
        self.models = {}
        self.connection = None
        
        self.create()
        
    def create(self, new=False):
        c = self.options
        
        db = self.engine_instance
        if not self.engine_instance or new:
            args = c.get('connection_args', {})
            self.engine_instance = create_engine(c.get('connection_string'), **args)
        self.engine_instance.echo = c['debug_log']
        self.engine_instance.metadata = self.metadata
        self.metadata.bind = self.engine_instance
            
        self.create_all()
        return self.engine_instance
        
    def create_all(self):
        for cls in self.models.values():
            if not cls['created'] and cls['model']:
                cls['model'].bind(self.metadata, auto_create=__auto_create__)
                cls['created'] = True
                
    def connect(self, **kwargs):
        return self.engine.connect(**kwargs)
    
    @property
    def engine(self):
        return self.engine_instance
    
class EngineManager(object):
    def __init__(self):
        self.engines = {}
        
    def add(self, name, connection):
        self.engines[name] = engine = NamedEngine(name, connection)
        return engine
        
    def get(self, name=None):
        name = name or 'default'
        
        engine = self.engines.get(name)
        if not engine:
            raise Error('Engine %s is not exists yet' % name)
        return engine
    
    def __getitem__(self, name=None):
        return self.get(name)
    
    def __setitem__(self, name, connection):
        return self.add(name, connection)
    
    def __contains__(self, name):
        return name in self.engines
    
engine_manager = EngineManager()

def print_pool_status(ec=None):
    ec = ec or 'default'
    engine = engine_manager[ec]
    if engine.engine.pool:
        print engine.engine.pool.status()
    
def get_connection(connection='', default=True, 
    debug=None, engine_name=None, connection_type='long', **args):
    """
    default encoding is utf-8
    """
    d = {
        'connection_string':connection,
        'debug_log':debug, 
        'connection_args':args,
        'connection_type':connection_type,
        }
    if connection:
        #will create new connection
        if default:
            engine_name = engine_name or 'default'
            engine = engine_manager.add(engine_name, d).engine
            reset_local_connection(engine_name)
        else:
            engine = NamedEngine('', d).engine
        return engine
    else:
        engine_name = engine_name or 'default'
        if engine_name in engine_manager:
            return engine_manager[engine_name].engine
        else:
            raise Error("Can't find engine %s" % engine_name)
        
def get_metadata(engine_name=None):
    """
    get metadata according used for alembic
    It'll import all tables
    """
    engine = engine_manager[engine_name]
    
    for tablename, m in engine.models.items():
        if not m['model']:
            get_model(tablename, engine_name)
    return engine.metadata

def local_conection(ec, auto_transaction=False):
    """
    :param: ec - engine_name or connection
    auto_transaction will only effect for named engine
    """
    global __auto_dotransaction__
    
    ec = ec or 'default'
    #if connection strategy is threadlocal then directly return db
    #but not connect
#    engine = engine_manager[ec]
#    if engine.options.connection_args['strategy'] == 'threadlocal':
#        return engine.engine_instance
    if isinstance(ec, (str, unicode)):
        if hasattr(Local, 'conn') and Local.conn.get(ec):
            conn = Local.conn[ec]
        else:
            engine = engine_manager[ec]
            conn = engine.connect()
            
            if not hasattr(Local, 'conn'):
                Local.conn = {}
            Local.conn[ec] = conn
        if __auto_dotransaction__ or auto_transaction:
            if not hasattr(Local, 'trans'):
                Local.trans = {}
            if not Local.trans.get(ec):
                Local.trans[ec] = conn.begin()
                
    elif isinstance(ec, EngineBase.Connection) or isinstance(ec, EngineBase.Engine):
        conn = ec
    else:
        raise Error("Connection %r should be existed engine name or valid Connection object" % ec)
    return conn
    
def reset_local_connection(ec):
    """
    """
    if hasattr(Local, 'conn') and Local.conn.get(ec):
        conn = Local.conn[ec]
        conn.close()
        engine = engine_manager[ec]
        Local.conn[ec] = None
    if hasattr(Local, 'trans') and Local.trans.get(ec):
        Local.trans[ec] = None

def Reset(ec=None):
    ec = ec or 'default'
    reset_local_connection(ec)
    
def ResetAll():
    if hasattr(Local, 'trans'):
        for k, v in Local.trans.items():
            Local.trans[k] = None
            
    if hasattr(Local, 'conn'):
        for k, v in Local.conn.items():
            v.close()
            Local.conn[k] = None

@dispatch.bind('post_do', kind=dispatch.LOW)
def default_post_do(sender, query, conn, usetime):
    if __default_post_do__:
        __default_post_do__(sender, query, conn, usetime)
       
def rawsql(query, ec=None):
    from MySQLdb.converters import conversions, escape
    if isinstance(query, Result):
        query = query.get_query()

    ec = ec or 'default'
    engine = engine_manager[ec]
    dialect = engine.engine.dialect
    enc = dialect.encoding
    comp = query.compile(dialect=dialect)
    params = []
    for k in comp.positiontup:
        v = comp.params[k]
        if isinstance(v, unicode):
            v = v.encode(enc)
        params.append( escape(v, conversions) )
    return (comp.string.encode(enc).replace('?', '%s') % tuple(params))
    
    
def do_(query, ec=None, args=None):
    """
    Execute a query
    if auto_transaction is True, then if there is no connection existed,
    then auto created an connection, and auto begin transaction
    """
    from time import time
    from uliweb.utils.common import get_caller
    
    conn = local_conection(ec)
    b = time()
    result = conn.execute(query, *(args or ()))
    t = time() - b
    dispatch.call(ec, 'post_do', query, conn, t)
    
    flag = False
    sql = ''
    if hasattr(Local, 'echo') and Local.echo:
        if hasattr(Local, 'echo_args') and Local.echo_args['time']:
            if t >= Local.echo_args['time']:
                sql = rawsql(query)
                
                flag = True
        else:
            sql = rawsql(query)
            flag = True
        
        if flag:
            Local.echo_func('\n===>>>>> ')
            if hasattr(Local, 'echo_args') and Local.echo_args['caller']:
                v = get_caller(skip=__file__)
                Local.echo_func('(%s:%d:%s)\n' % v)
            else:
                Local.echo_func('\n')
            Local.echo_func(sql)
            if hasattr(Local, 'echo_args') and Local.echo_args['explain'] and sql:
                r = conn.execute('explain '+sql).fetchone()
                Local.echo_func('\n----\nExplain: %s' % ''.join(["%s=%r, " % (k, v) for k, v in r.items()]))
            Local.echo_func('\n===<<<<< time used %fs\n\n' % t)
                
    return result

def save_file(result, filename, encoding='utf8', visitor=None):
    """
    save query result to a csv file
    visitor can used to convert values, all value should be convert to string
    visitor function should be defined as:
        def visitor(keys, values, encoding):
            #return new values []
    """
    import csv
    from uliweb.utils.common import simple_value
    
    with open(filename, 'wb') as f:
        w = csv.writer(f)
        w.writerow(result.keys())
        for row in result:
            if visitor and callable(visitor):
                _row = visitor(result.keys, row.values(), encoding)
            else:
                _row = row
            r = [simple_value(x, encoding=encoding) for x in _row]
            w.writerow(r)
    
def Begin(ec=None):
    ec = ec or 'default'
    if isinstance(ec, (str, unicode)):
        conn = local_conection(ec, True)
        return Local.trans[ec]
    elif isinstance(ec, EngineBase.Connection):
        return ec.begin()
    else:
        raise Error("Connection %r should be existed engine name or valid Connection object" % ec)
    
def Commit(close=False, ec=None, trans=None):
    ec = ec or 'default'
    if isinstance(ec, (str, unicode)):
        if hasattr(Local, 'trans') and Local.trans.get(ec):
            try:
                Local.trans[ec].commit()
            finally:
                Local.trans[ec] = None
                if close:
                    Local.conn[ec].close()
                    Local.conn[ec] = None
    elif isinstance(ec, EngineBase.Connection):
        trans.commit()
        if close:
            ec.close()
    else:
        raise Error("Connection %r should be existed engine name or valid Connection object" % ec)

def CommitAll(close=False):
    """
    Commit all transactions according Local.conn
    """
    if hasattr(Local, 'trans'):
        for k, v in Local.trans.items():
            if v:
                v.commit()
                Local.trans[k] = None
            
    if close and hasattr(Local, 'conn'):
        for k, v in Local.conn.items():
            if v:
                v.close()
                Local.conn[k] = None
            
def Rollback(close=False, ec=None, trans=None):
    ec = ec or 'default'
    
    if isinstance(ec, (str, unicode)):
        if hasattr(Local, 'trans') and Local.trans.get(ec):
            try:
                Local.trans[ec].rollback()
            finally:
                Local.trans[ec] = None
                if close:
                    Local.conn[ec].close()
                    Local.conn[ec] = None
    elif isinstance(ec, EngineBase.Connection):
        trans.rollback()
        if close:
            ec.close()
    else:
        raise Error("Connection %r should be existed engine name or valid Connection object" % ec)

def RollbackAll(close=False):
    """
    Rollback all transactions, according Local.conn
    """
    if hasattr(Local, 'trans'):
        for k, v in Local.trans.items():
            if v:
                v.rollback()
                Local.trans[k] = None
            
    if close and hasattr(Local, 'conn'):
        for k, v in Local.conn.items():
            if v:
                v.close()
                Local.conn[k] = None
    
def check_reserved_word(f):
    if f in ['put', 'save', 'table', 'tablename'] or f in dir(Model):
        raise ReservedWordError(
            "Cannot define property using reserved word '%s'. " % f
            )

#def create_all(db=None, engine_name=None):
#    engine = engine_manager.get_engine(engine_name)
#    for cls in engine.options['__models__'].values():
#        if not cls['created'] and cls['model']:
#            cls['model'].bind(engine.options['metadata'], auto_create=__auto_create__)
#            cls['created'] = True
        
def set_model(model, tablename=None, created=None, engine_name=None):
    """
    Register an model and tablename to a global variable.
    model could be a string format, i.e., 'uliweb.contrib.auth.models.User'
    
    item structure
        created
        model
        model_path
        appname
    """
    if isinstance(model, type) and issubclass(model, Model):
        #use alias first
        tablename = model.__alias__ or model.tablename
    tablename = tablename.lower()
    item = {}
    if created is not None:
        item['created'] = created
    else:
        item['created'] = None
    if isinstance(model, (str, unicode)):
        model_path = model
        appname = model.rsplit('.', 2)[0]
        #for example 'uliweb.contrib.auth.models.User'
        model = None
    else:
        appname = model.__module__.rsplit('.', 1)[0]
        model_path = model.__module__ + '.' + model.__name__
        #for example 'uliweb.contrib.auth.models'
        
    item['model'] = model
    item['model_path'] = model_path
    item['appname'] = appname
    
    engine_name = engine_name or 'default'
    if not isinstance(engine_name, (str, unicode)):
        raise BadValueError('engine name should be string type, but %r found' % engine_name)
    
    engine_manager[engine_name].models[tablename] = item
    
    #set global __models__
    d = __models__.setdefault(tablename, {})
    d['model_path'] = model_path
    d['engine_name'] = engine_name
    
    __model_paths__[model_path] = engine_name
    
def set_model_config(model_name, config):
    """
    This function should be only used in initialization phrase
    :param model_name: model name it's should be string
    :param config: config should be dict. e.g. {'__mapping_only__':xxx}
    """
    assert isinstance(model_name, str)
    assert isinstance(config, dict)
    
    if model_name not in __models__:
        raise ConfigurationError("Can't find mode %s" % model_name)
    __models__[model_name]['config'] = config
    
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
#    Model.__engine_name__ could be a list, so if there are multiple then use
#    the first one
#    """
#    tablename = model.__alias__ or model.tablename
#    name = model.__name__
#    appname = model.__module__
#    model_path = appname + '.' + name
#    return (tablename not in __models__) or (model_path in __model_paths__)
#
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
    
#def clone_model(model, ec=None):
#    ec = ec or default
#    name = '%s_%s' % (ec, model.__name__)
#    cls = type(name, (model,), {'__tablename__':model.tablename, '__bind__':False})
#    cls.__module__ = model.__module__
#    return cls

def get_model(model, engine_name=None):
    """
    Return a real model object, so if the model is already a Model class, then
    return it directly. If not then import it.

    if engine_name is None, then it'll find other engine_name according __models__
    """
    if model is _SELF_REFERENCE:
        return model
    if isinstance(model, type) and issubclass(model, Model):
        return model
    if not isinstance(model, (str, unicode)):
        raise Error("Model %r should be string or unicode type" % model)
    
    #make model name is lower case
    model = model.lower()
    if model in __models__:
        engine_name = __models__[model]['engine_name']
        engine = engine_manager[engine_name]
        if model in engine.models:
            item = engine.models[model]
            m = item['model']
            if isinstance(m, type) and issubclass(m, Model):
                m.connect(engine_name)
#                m.bind(engine.metadata)
                return m
            else:
                m, name = item['model_path'].rsplit('.', 1)
                mod = __import__(m, fromlist=['*'])
                model_inst = getattr(mod, name)
                config = __models__[model].get('config', {})
                if config:
                    for k, v in config.items():
                        setattr(model_inst, k, v)
                item['model'] = model_inst
                model_inst.__alias__ = model
                model_inst.connect(engine_name)
                
                #todo add property init process
                for k, v in model_inst.properties.items():
                    v.__property_config__(model_inst, k)
                #add bind process
                model_inst.bind(engine.metadata)
                return model_inst
    raise Error("Can't found the model %s in engine %s" % (model, engine_name))
    
def get_object(table, id, cache=False, fields=None):
    """
    Get obj in Local.object_caches first and also use get_cached function if 
    not found in object_caches
    """
    
    if isinstance(table, (str, unicode)):
        model = get_model(table)
    else:
        model = table
      
    if cache:
        obj = model.get_cached(id, fields=fields)
    else:
        obj = model.get(id, fields=fields)
    
    return obj
        
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

class ModelMetaclass(type):
    def __init__(cls, name, bases, dct):
        super(ModelMetaclass, cls).__init__(name, bases, dct)
        if name == 'Model':
            return
        cls._set_tablename()
        
        #check if cls is matched with __models__ module_path
        if not check_model_class(cls):
            return
        
        cls.properties = {}
        cls._fields_list = []
        defined = set()
        for base in bases:
            if hasattr(base, 'properties'):
#                property_keys = base.properties.keys()
#                duplicate_properties = defined.intersection(property_keys)
#                if duplicate_properties:
#                    raise DuplicatePropertyError(
#                        'Duplicate properties in base class %s already defined: %s' %
#                        (base.__name__, list(duplicate_properties)))
#                defined.update(property_keys)
                cls.properties.update(base.properties)
        
        cls._manytomany = {}
        for attr_name in dct.keys():
            attr = dct[attr_name]
            if isinstance(attr, Property):
                cls.add_property(attr_name, attr, set_property=False, config=not __lazy_model_init__)
                
                if isinstance(attr, ManyToMany):
                    cls._manytomany[attr_name] = attr
         
        #if there is already defined primary_key, the id will not be primary_key
        has_primary_key = bool([v for v in cls.properties.itervalues() if 'primary_key' in v.kwargs])
        
        #add __without_id__ attribute to model, if set it, uliorm will not
        #create 'id' field for the model
        without_id = getattr(cls, '__without_id__', False)
        if 'id' not in cls.properties and not without_id:
            cls.properties['id'] = f = Field(PKTYPE(), autoincrement=True, 
                primary_key=not has_primary_key, default=None, nullable=False, server_default=None)
            if not __lazy_model_init__:
                f.__property_config__(cls, 'id')
            setattr(cls, 'id', f)

#        fields_list = [(k, v) for k, v in cls.properties.items() if not isinstance(v, ManyToMany)]
        fields_list = [(k, v) for k, v in cls.properties.items()]
        fields_list.sort(lambda x, y: cmp(x[1].creation_counter, y[1].creation_counter))
        cls._fields_list = fields_list
        
        if cls.__bind__ and not __lazy_model_init__:
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
    creation_counter = 0
    property_type = 'column'   #Property type: 'column', 'compound', 'relation'
    server_default = None
    
    def __init__(self, verbose_name=None, name=None, default=None,
        required=False, validators=None, choices=None, max_length=None, 
        hint='', auto=None, auto_add=None, type_class=None, type_attrs=None, 
        placeholder='', extra=None,
        sequence=False, **kwargs):
        self.verbose_name = verbose_name
        self.property_name = None
        self.name = name
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
        for k in ['verbose_name', 'required', 'hint', 'placeholder', 'choices',
            'default', 'validators', 'max_length']:
            d[k] = getattr(self, k)
        return d
        
    def create(self, cls):
        global __nullable__
        
        kwargs = self.kwargs.copy()
        kwargs['key'] = self.name
#        if callable(self.default):
#            kwargs['default'] = self.default()
#        kwargs['default'] = self.default
        kwargs['primary_key'] = self.kwargs.get('primary_key', False)
        kwargs['autoincrement'] = self.kwargs.get('autoincrement', False)
        kwargs['index'] = self.kwargs.get('index', False)
        kwargs['unique'] = self.kwargs.get('unique', False)
        #nullable default change to False
        kwargs['nullable'] = self.kwargs.get('nullable', __nullable__)
        if __server_default__:
            kwargs['server_default' ] = self.kwargs.get('server_default', self.server_default)
        else:
            kwargs['server_default' ] = self.kwargs.get('server_default', None)
        
        f_type = self._create_type()
        args = ()
        if self.sequence:
            args = (self.sequence, )

        return Column(self.property_name, f_type, *args, **kwargs)

    def _create_type(self):
        if self.max_length:
            f_type = self.type_class(self.max_length, **self.type_attrs)
        else:
            f_type = self.type_class(**self.type_attrs)
        return f_type
    
    def __property_config__(self, model_class, property_name):
        self.model_class = model_class
        self.property_name = property_name
        if not self.name:
            self.name = property_name
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
            _id = getattr(model_instance, 'id')
            if not _id:
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

    def validate(self, value):
        if self.empty(value):
            if self.required:
                raise BadValueError('Property %s is required' % self.name)
#        else:
#            if self.choices:
#                match = False
#                choices = self.get_choices()
#                for choice in choices:
#                    if isinstance(choice, tuple):
#                        if choice[0] == value:
#                            match = True
#                    else:
#                        if choice == value:
#                            match = True
#                    if match:
#                        break
#                if not match:
#                    c = []
#                    for choice in choices:
#                        if isinstance(choice, tuple):
#                            c.append(choice[0])
#                        else:
#                            c.append(choice)
#                    raise BadValueError('Property %s is %r; must be one of %r' %
#                        (self.name, value, c))
        #skip Lazy value
        if value is Lazy:
            return value
        
        if value is not None:
            try:
                value = self.convert(value)
            except TypeError, err:
                raise BadValueError('Property %s must be convertible '
                    'to %s, but the value is (%s)' % (self.name, self.data_type, err))
            
            if hasattr(self, 'custom_validate'):
                value = self.custom_validate(value)
                
        for v in self.validators:
            v(value)
        return value

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
    
    def __repr__(self):
        return ("<%s 'type':%r, 'verbose_name':%r, 'name':%r, " 
            "'default':%r, 'required':%r, 'validator':%r, "
            "'chocies':%r, 'max_length':%r, 'kwargs':%r>"
            % (
            self.__class__.__name__,
            self.data_type, 
            self.verbose_name,
            self.name,
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
    
class CharProperty(Property):
    data_type = unicode
    field_class = CHAR
    server_default=''
    
    def __init__(self, verbose_name=None, default=u'', max_length=None, **kwds):
        if __check_max_length__ and not max_length:
            raise BadPropertyTypeError("max_length parameter not passed for property %s" % self.__class__.__name__)
        max_length = max_length or 255
        super(CharProperty, self).__init__(verbose_name, default=default, max_length=max_length, **kwds)
    
    def convert(self, value):
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
        return v
    
class StringProperty(CharProperty):
    field_class = VARCHAR
    
class FileProperty(StringProperty):
    def __init__(self, verbose_name=None, max_length=None, upload_to=None, upload_to_sub=None, **kwds):
        max_length = max_length or 255
        super(FileProperty, self).__init__(verbose_name, max_length=max_length, **kwds)
        self.upload_to = upload_to
        self.upload_to_sub = upload_to_sub
        
class UnicodeProperty(CharProperty):
    field_class = Unicode
    
class TextProperty(Property):
    field_class = Text
    data_type = unicode
    
    def __init__(self, verbose_name=None, default='', **kwds):
        super(TextProperty, self).__init__(verbose_name, default=default, max_length=None, **kwds)
    
    def convert(self, value):
        if isinstance(value, str):
            return unicode(value, __default_encoding__)
        else:
            return self.data_type(value)
    
class BlobProperty(Property):
    field_class = BLOB
    data_type = str
    
    def __init__(self, verbose_name=None, default='', **kwds):
        super(BlobProperty, self).__init__(verbose_name, default=default, max_length=None, **kwds)
    
    def get_display_value(self, value):
        return repr(value)
    
    def convert(self, value):
        return value
    
class PickleProperty(BlobProperty):
    field_class = PickleType
    data_type = None
    
class DateTimeProperty(Property):
    data_type = datetime.datetime
    field_class = DateTime
    server_default = '0000-00-00 00:00:00'
    
    def __init__(self, verbose_name=None, auto_now=False, auto_now_add=False,
            format=None, **kwds):
        super(DateTimeProperty, self).__init__(verbose_name, **kwds)
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
    
    def __init__(self, verbose_name=None, default=0, **kwds):
        super(IntegerProperty, self).__init__(verbose_name, default=default, **kwds)
    
    def custom_validate(self, value):
        if value and not isinstance(value, (int, long, bool)):
            raise BadValueError('Property %s must be an int, long or bool, not a %s'
                % (self.name, type(value).__name__))
        return value

class BigIntegerProperty(IntegerProperty):
    field_class = BigInteger
    
class FloatProperty(Property):
    """A float property."""

    data_type = float
    field_class = Float
    server_default=text('0')
    
    def __init__(self, verbose_name=None, default=0.0, precision=None, **kwds):
        super(FloatProperty, self).__init__(verbose_name, default=default, **kwds)
        self.precision = precision
        
    def _create_type(self):
        f_type = self.type_class(precision=self.precision, **self.type_attrs)
        return f_type
    
    def custom_validate(self, value):
        if value and not isinstance(value, float):
            raise BadValueError('Property %s must be a float, not a %s' 
                % (self.name, type(value).__name__))
        if abs(value) < __zero_float__:
            value = 0.0
        return value
    
class DecimalProperty(Property):
    """A float property."""

    data_type = decimal.Decimal
    field_class = Numeric
    server_default=text('0.00')
    
    def __init__(self, verbose_name=None, default='0.0', precision=10, scale=2, **kwds):
        super(DecimalProperty, self).__init__(verbose_name, default=default, **kwds)
        self.precision = precision
        self.scale = scale
   
    def custom_validate(self, value):
        if value is not None and not isinstance(value, decimal.Decimal):
            raise BadValueError('Property %s must be a decimal, not a %s'
                % (self.name, type(value).__name__))
        return value
    
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
    
class BooleanProperty(Property):
    """A boolean property."""

    data_type = bool
    field_class = Boolean
    server_default=text('0')
    
    def __init__(self, verbose_name=None, default=False, **kwds):
        super(BooleanProperty, self).__init__(verbose_name, default=default, **kwds)
    
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

    def __init__(self, reference_class=None, verbose_name=None, collection_name=None, 
        reference_fieldname=None, required=False, engine_name=None, **attrs):
        """Construct ReferenceProperty.

        Args:
            reference_class: Which model class this property references.
            verbose_name: User friendly name of property.
            collection_name: If provided, alternate name of collection on
                reference_class to store back references.    Use this to allow
                a Model to have multiple fields which refer to the same class.
            reference_fieldname used to specify which fieldname of reference_class
                should be referenced
        """
        super(ReferenceProperty, self).__init__(verbose_name, **attrs)

        self._collection_name = collection_name
        self.reference_fieldname = reference_fieldname or 'id'
        self.required = required
        self.engine_name = engine_name

        if reference_class is None:
            reference_class = Model
            
        self.reference_class = reference_class
        
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
#        return Column(self.property_name, f_type, ForeignKey("%s.id" % self.reference_class.tablename), **args)
        if __server_default__:
            if self.data_type is int or self.data_type is long :
                args['server_default'] = text('0')
            else:
                args['server_default'] = self.reference_field.kwargs.get('server_default')
        return Column(self.property_name, f_type, **args)
    
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
        
        if self.reference_class is _SELF_REFERENCE:
            self.reference_class = model_class
        else:
            self.reference_class = get_model(self.reference_class, self.engine_name)
            
        self.collection_name = self.reference_class.get_collection_name(self._collection_name, model_class.tablename)
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

    def _id_attr_name(self):
        """Get attribute of referenced id.
        #todo add id function or key function to model
        """
        return self.reference_fieldname

    def _resolved_attr_name(self):
        """Get attribute of resolved attribute.

        The resolved attribute is where the actual loaded reference instance is
        stored on the referring model instance.

        Returns:
            Attribute name of where to store resolved reference model instance.
        """
        return '_RESOLVED' + self._attr_name()

Reference = ReferenceProperty

class OneToOne(ReferenceProperty):
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
#        return Column(self.property_name, f_type, ForeignKey("%s.id" % self.reference_class.tablename), **args)
        if __server_default__:
            if self.data_type is int or self.data_type is long :
                args['server_default'] = text('0')
            else:
                args['server_default'] = self.reference_field.kwargs.get('server_default')
        return Column(self.property_name, f_type, **args)

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
            self.reference_class = get_model(self.reference_class, self.engine_name)

        self.collection_name = self._collection_name
        if self.collection_name is None:
            self.collection_name = '%s' % (model_class.tablename)
        if hasattr(self.reference_class, self.collection_name):
            raise DuplicatePropertyError('Class %s already has property %s'
                 % (self.reference_class.__name__, self.collection_name))
        setattr(self.reference_class, self.collection_name,
            _OneToOneReverseReferenceProperty(model_class, property_name, self._id_attr_name()))
  
def get_objs_columns(objs, field='id'):
    ids = []
    new_objs = []
    for x in objs:
        if isinstance(x, (tuple, list)):
            new_objs.extend(x)
        else:
            new_objs.append(x)
            
    for o in new_objs:
        if not isinstance(o, Model):
            _id = o
        else:
            _id = o.get_datastore_value(field)
        if _id not in ids:
            ids.append(_id)
    return ids

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
        self.distinct_field = None
        self._values_flag = False
        self.connection = model.get_connection()
        
    def do_(self, query):
        global do_
        return do_(query, self.connection)
    
    def get_column(self, model, fieldname):
        if isinstance(fieldname, (str, unicode)):
            if issubclass(model, Model):
                v = fieldname.split('.')
                if len(v) > 1:
                    field = get_model(v[0]).table.c(v[1])
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
                    field = get_model(v[0]).properties(v[1])
                else:
                    field = model.properties[col]
            elif isinstance(col, Column):
                field = get_model(col.table.name).properties[col.name]
            else:
                field = col
            
            fields.append(field)
        
        return fields
        
    def connect(self, connection):
        if connection:
            self.connection = connection
        return self
        
    def all(self):
        return self
    
    def get(self, condition=None):
        if isinstance(condition, (int, long)):
            return self.filter(self.model.c.id==condition).one()
        else:
            return self.filter(condition).one()
    
    def count(self):
        flag = False
        #judge if there is a distince process
        for name, args, kwargs in self.funcs:
            if name == 'distinct':
                flag = True
                break
        if not flag:
            return self.model.count(self.condition)
        else:
            sql = select([func.count(func.distinct(self.model.c.id))], self.condition)
            return self.do_(sql).scalar()

    def filter(self, *condition):
        """
        If there are multple condition, then treats them *and* relastion.
        """
        if not condition:
            return self
        cond = None
        for c in condition:
            if c is not None:
                cond = c & cond
        if self.condition is not None:
            self.condition = cond & self.condition
        else:
            self.condition = cond
        return self
    
    def order_by(self, *args, **kwargs):
        self.funcs.append(('order_by', args, kwargs))
        return self
    
    def group_by(self, *args):
        self._group_by = args
        return self
    
    def fields(self, *args, **kwargs):
        if args:
            args = flat_list(args)
            if args:
                if 'id' not in args:
                    args.append('id')
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
        return self

    def offset(self, *args, **kwargs):
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
    
    def save_file(self, filename, encoding='utf8', display=True):
        """
        save result to a csv file.
        display = True will convert value according choices value
        """
        global save_file
        
        if display:
            fields = self.get_fields()
            def visitor(keys, values, encoding):
                r = []
                for i, column in enumerate(fields):
                    r.append(column.get_display_value(values[i]))
                return r
        else:
            visitor = None
        return save_file(self.run(), filename, encoding=encoding, visitor=visitor)
    
    def get_query(self):
        #user can define default_query, and default_query 
        #should be class method
        if self.default_query_flag:
            _f = getattr(self.model, 'default_query', None)
            if _f:
                _f(self)
        if self.condition is not None:
            query = select(self.get_columns(), self.condition, **self.kwargs)
        else:
            query = select(self.get_columns(), **self.kwargs)
        for func, args, kwargs in self.funcs:
            query = getattr(query, func)(*args, **kwargs)
        if self._group_by:
            query = query.group_by(*self._group_by)
        return query
    
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
    
    def clear(self):
        return self.model.remove(self.condition)
    
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
        self.distinct_field = None
        self._values_flag = False
        self.connection = model.get_connection()
        
    def has(self, *objs):
        ids = get_objs_columns(objs)
        
        if not ids:
            return False
        
        count = self.do_(self.model.table.count(self.condition & (self.model.table.c['id'].in_(ids)))).scalar()
        return count > 0
    
    def ids(self):
        query = select([self.model.c['id']], self.condition)
        ids = [x[0] for x in self.do_(query)]
        return ids
    
    def clear(self, *objs):
        """
        Clear the third relationship table, but not the ModelA or ModelB
        """
        if objs:
            ids = get_objs_columns(objs)
            self.do_(self.model.table.delete(self.condition & self.model.table.c['id'].in_(ids)))
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
        self.condition = None
        self.funcs = []
        self.result = None
        self.with_relation_name = None
        self.through_model = through_model
        self.default_query_flag = True
        self._group_by = None
        self.distinct_field = None
        self._values_flag = False
        self.connection = self.modela.get_connection()
        self.kwargs = {}
        
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
    
    def update(self, *objs):
        """
        Update the third relationship table, but not the ModelA or ModelB
        """
        ids = self.ids()
        new_ids = get_objs_columns(objs, self.realfieldb)

        modified = False
        for v in new_ids:
            if v in ids:    #the id has been existed, so don't insert new record
                ids.remove(v)
            else:
                d = {self.fielda:self.valuea, self.fieldb:v}
                if self.through_model:
                    obj = self.through_model(**d)
                    obj.save()
                else:
                    self.do_(self.table.insert().values(**d))
                modified = True
                
        if ids: #if there are still ids, so delete them
            self.clear(*ids)
            modified = True
        
        #cache [] to _STORED_attr_name
        setattr(self.instance, self.store_key, new_ids)
        
        return modified
            
    def clear(self, *objs):
        """
        Clear the third relationship table, but not the ModelA or ModelB
        """
        if objs:
            ids = get_objs_columns(objs, self.realfieldb)
            self.do_(self.table.delete((self.table.c[self.fielda]==self.valuea) & (self.table.c[self.fieldb].in_(ids))))
        else:
            self.do_(self.table.delete(self.table.c[self.fielda]==self.valuea))
        #cache [] to _STORED_attr_name
        setattr(self.instance, self.store_key, Lazy)
        
    remove = clear
    
    def count(self):
        result = self.table.count((self.table.c[self.fielda]==self.valuea) & (self.table.c[self.fieldb] == self.modelb.c[self.realfieldb]) & self.condition).execute()
        count = 0
        if result:
            r = result.fetchone()
            if r:
                count = r[0]
        else:
            count = 0
        return count
    
    def has(self, *objs):
        ids = get_objs_columns(objs, self.realfieldb)
        
        if not ids:
            return False
        
        count = self.do_(self.table.count((self.table.c[self.fielda]==self.valuea) & (self.table.c[self.fieldb].in_(ids)))).scalar()
        return count > 0
        
    def fields(self, *args, **kwargs):
        if args:
            args = flat_list(args)
            if args:
                if 'id' not in args:
                    args.append('id')
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
            raise Error, "The attribute name %s has already existed in Model %s!" % (relation_name, self.modelb.__name__)
        if not self.through_model:
            raise Error, "Only with through style in ManyToMany supports with_relation function of Model %s!" % self.modelb.__name__
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
    def __init__(self, reference_class=None, verbose_name=None, collection_name=None, 
        reference_fieldname=None, reversed_fieldname=None, required=False, through=None, 
        through_reference_fieldname=None, through_reversed_fieldname=None, 
        reversed_manytomany_fieldname=None, **attrs):
        """
        Definition of ManyToMany property
        
        :param through_field_from: relative to field of A 
        :param through_field_to: relative to field of B 
        :param index_reverse: create index reversed
        """
            
        super(ManyToMany, self).__init__(reference_class=reference_class,
            verbose_name=verbose_name, collection_name=collection_name, 
            reference_fieldname=reference_fieldname, required=required, **attrs)
    
        self.reversed_fieldname = reversed_fieldname or 'id'
        self.through = through
        self.through_reference_fieldname = through_reference_fieldname
        self.through_reversed_fieldname = through_reversed_fieldname
        self.index_reverse = attrs['index_reverse'] if 'index_reverse' in attrs else __manytomany_index_reverse__

    def create(self, cls):
#        if self.through:
#            if not (
#                    (isinstance(self.through, type) and issubclass(self.reference_class, Model)) or
#                    valid_model(self.reference_class)):
#                raise KindError('through must be Model or available table name')
#            self.through = get_model(self.through)
#            for k, v in self.through.properties.items():
#                if isinstance(v, ReferenceProperty):
#                    if self.model_class is v.reference_class:
#                        self.fielda = k
#                        self.reversed_fieldname = v.reference_fieldname
#                    elif self.reference_class is v.reference_class:
#                        self.fieldb = k
#                        self.reference_fieldname = v.reference_fieldname
#            if not hasattr(self.through, self.fielda):
#                raise BadPropertyTypeError("Can't find %s in Model %r" % (self.fielda, self.through))
#            if not hasattr(self.through, self.fieldb):
#                raise BadPropertyTypeError("Can't find %s in Model %r" % (self.fieldb, self.through))
#            self.table = self.through.table
        if not self.through:
            self.fielda = "%s_id" % self.model_class.tablename
            #test model_a is equels model_b
            if self.model_class.tablename == self.reference_class.tablename:
                _t = self.reference_class.tablename + '_b'
            else:
                _t = self.reference_class.tablename
            self.fieldb = "%s_id" % _t
            self.table = self.create_table()
            #add appname to self.table
            appname = self.model_class.__module__
            self.table.__appname__ = appname[:appname.rfind('.')]
            self.model_class.manytomany.append(self.table)
            index_name = '%s_mindx' % self.tablename
            if index_name not in [x.name for x in self.table.indexes]:
                Index(index_name, self.table.c[self.fielda], self.table.c[self.fieldb], unique=True)
                #add field_b index
                if self.index_reverse:
                    Index('%s_rmindx' % self.tablename, self.table.c[self.fieldb])

            #process __mapping_only__ property, if the modela or modelb is mapping only
            #then manytomany table will be mapping only
            if getattr(self.model_class, '__mapping_only__', False) or getattr(self.reference_class, '__mapping_only__', False):
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
        if self.through and (not isinstance(self.through, type) or not issubclass(self.through, Model)):
            if not (
                    (isinstance(self.through, type) and issubclass(self.reference_class, Model)) or
                    valid_model(self.reference_class)):
                raise KindError('through must be Model or available table name')
            self.through = get_model(self.through)
            for k, v in self.through.properties.items():
                find = False
                if isinstance(v, ReferenceProperty):
                    if self.model_class is v.reference_class:
                        if self.through_reversed_fieldname:
                            if k == self.through_reversed_fieldname:
                                find = True
                        else:
                            find = True
                        if find:
                            self.fielda = k
                            self.reversed_fieldname = v.reference_fieldname
                    elif self.reference_class is v.reference_class:
                        if self.through_reference_fieldname:
                            if k == self.through_reference_fieldname:
                                find = True
                        else:
                            find = True
                        if find:
                            self.fieldb = k
                            self.reference_fieldname = v.reference_fieldname
            if not hasattr(self.through, self.fielda):
                raise BadPropertyTypeError("Can't find %s in Model %r" % (self.fielda, self.through))
            if not hasattr(self.through, self.fieldb):
                raise BadPropertyTypeError("Can't find %s in Model %r" % (self.fieldb, self.through))
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
        
        if self.reference_class is _SELF_REFERENCE:
            self.reference_class = self.data_type = model_class
        else:
            self.reference_class = get_model(self.reference_class, self.engine_name)

        self.tablename = '%s_%s_%s' % (model_class.tablename, self.reference_class.tablename, property_name)
        self.collection_name = self.reference_class.get_collection_name(self._collection_name, model_class.tablename)
        setattr(self.reference_class, self.collection_name,
            _ManyToManyReverseReferenceProperty(self, self.collection_name))
    
    def get_lazy(self, model_instance, name, default=None):
        v = self.get_attr(model_instance, name, default)
        if v is Lazy:
#            _id = getattr(model_instance, 'id')
#            if not _id:
#                raise BadValueError('Instance is not a validate object of Model %s, ID property is not found' % model_instance.__class__.__name__)
            result = getattr(model_instance, self.name)
            v = result.ids(True)
            setattr(model_instance, name, v)
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
            value = get_objs_columns(value, self.reference_fieldname)
        setattr(model_instance, self._attr_name(), value)
    
    def get_value_for_datastore(self, model_instance, cached=False):
        """Get key of reference rather than reference itself."""
        value = getattr(model_instance, self._attr_name(), None)
        if not cached:
            value = getattr(model_instance, self.property_name).ids()
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
            ids = get_objs_columns(objs, self.reference_fieldname)
            sub_query = select([self.table.c[self.fielda]], (self.table.c[self.fieldb] == self.reference_class.c[self.reference_fieldname]) & (self.table.c[self.fieldb].in_(ids)))
            condition = self.model_class.c[self.reversed_fieldname].in_(sub_query)
            return condition
         
    def join_in(self, *objs):
        """
        Create a join condition, connect A and C
        """
        if not objs:
            return self.table.c[self.fielda]!=self.table.c[self.fielda]
        else:
            ids = get_objs_columns(objs, self.reference_fieldname)
            return (self.table.c[self.fielda] == self.model_class.c[self.reversed_fieldname]) & (self.table.c[self.fieldb].in_(ids))
   
    def join_right_in(self, *objs):
        """
        Create a join condition, connect B and C
        """
        if not objs:
            return self.table.c[self.fielda]!=self.table.c[self.fielda]
        else:
            ids = get_objs_columns(objs, self.reference_fieldname)
            return (self.table.c[self.fieldb] == self.reference_class.c[self.reference_fieldname]) & (self.table.c[self.fielda].in_(ids))
    
    def filter(self, *condition):
        cond = None
        for c in condition:
            if c is not None:
                cond = c & cond
        sub_query = select([self.table.c[self.fielda]], (self.table.c[self.fieldb] == self.reference_class.c[self.reference_fieldname]) & cond)
        condition = self.model_class.c[self.reversed_fieldname].in_(sub_query)
        return condition

    def join_filter(self, *condition):
        cond = None
        for c in condition:
            if c is not None:
                cond = c & cond
        return (self.table.c[self.fielda] == self.model_class.c[self.reversed_fieldname]) & (self.table.c[self.fieldb] == self.reference_class.c[self.reference_fieldname]) & cond
        
def SelfReferenceProperty(verbose_name=None, collection_name=None, **attrs):
    """Create a self reference.
    """
    if 'reference_class' in attrs:
        raise ConfigurationError(
                'Do not provide reference_class to self-reference.')
    return ReferenceProperty(_SELF_REFERENCE, verbose_name, collection_name, **attrs)

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
    def __init__(self, model, reference_id, reversed_id):
        """Constructor for reverse reference.
    
        Constructor does not take standard values of other property types.
    
        """
        self._model = model
        self._reference_id = reference_id    #B Reference(A) this is B's id
        self._reversed_id = reversed_id    #A's id

    def __get__(self, model_instance, model_class):
        """Fetches collection of model instances of this collection property."""
        if model_instance:
            _id = getattr(model_instance, self._reversed_id, None)
            if _id is not None:
                b_id = self._reference_id
                d = self._model.c[self._reference_id]
                return self._model.get(d==_id)
            else:
                return None
        else:
            return self
    
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
BIGINT = BigIntegerProperty

_fields_mapping = {
    str:StringProperty,
    CHAR:CharProperty,
    unicode: UnicodeProperty,
    TEXT:TextProperty,
    BLOB:BlobProperty,
    FILE:FileProperty,
    int:IntegerProperty,
    BIGINT:BigIntegerProperty,
    float:FloatProperty,
    bool:BooleanProperty,
    datetime.datetime:DateTimeProperty,
    datetime.date:DateProperty,
    datetime.time:TimeProperty,
    decimal.Decimal:DecimalProperty,
    DECIMAL:DecimalProperty,
    PICKLE:PickleProperty,
}
def Field(type, *args, **kwargs):
    t = _fields_mapping.get(type, type)
    return t(*args, **kwargs)

class Model(object):

    __metaclass__ = ModelMetaclass
    __dispatch_enabled__ = True
    __engine_name__ = None
    __connection__ = None
    __alias__ = None #can be used via get_model(alias)
    __collection_set_id__ = 1
    __bind__ = True
    
    _lock = threading.Lock()
    _c_lock = threading.Lock()
    
    def __init__(self, **kwargs):
        self._old_values = {}
        
        self._load(kwargs)
        
    def set_saved(self):
        self._old_values = self.to_dict()
        for k, v in self.properties.items():
            if isinstance(v, ManyToMany):
                t = v.get_value_for_datastore(self, cached=True)
                if not t is Lazy:
                    self._old_values[k] = t
        
    def to_dict(self, fields=None, convert=True, manytomany=False):
        d = {}
        fields = fields or []
        for k, v in self.properties.items():
            if fields and not k in fields:
                continue
            if not isinstance(v, ManyToMany):
                t = v.get_value_for_datastore(self)
                if isinstance(t, Model):
                    t = t.id
                if convert:
                    d[k] = self.field_str(t)
                else:
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
           
    def _get_data(self):
        """
        Get the changed property, it'll be used to save the object
        """
        if self.id is None:
            d = {}
            for k, v in self.properties.items():
#                if not isinstance(v, ManyToMany):
                if v.property_type == 'compound':
                    continue
                if not isinstance(v, ManyToMany):
                    x = v.get_value_for_datastore(self)
                    if isinstance(x, Model):
                        x = x.id
                    elif x is None:
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
            d['id'] = self.id
            for k, v in self.properties.items():
                if v.property_type == 'compound':
                    continue
                t = self._old_values.get(k, None)
                if not isinstance(v, ManyToMany):
                    x = v.get_value_for_datastore(self)
                    #todo If need to support ManyToMany and Reference except id field?
                    if isinstance(x, Model):
                        x = x.id
                else:
                    x = v.get_value_for_datastore(self, cached=True)
                if t != self.field_str(x) and not x is Lazy:
                    d[k] = x
        
        return d
            
    def is_saved(self):
        return bool(self.id) 
    
    def update(self, **data):
        for k, v in data.iteritems():
            if k in self.properties:
                if not isinstance(self.properties[k], ManyToMany):
                    x = self.properties[k].get_value_for_datastore(self)
                    if self.field_str(x) != self.field_str(v):
                        setattr(self, k, v)
                else:
                    setattr(self, k, v)
        return self
#                    getattr(self, k).update(*v)
            
    def put(self, insert=False, connection=None, changed=None, saved=None, send_dispatch=True):
        """
        If insert=True, then it'll use insert() indead of update()
        
        changed will be callback function, only when the non manytomany properties
        are saved, the signature is:
            
            def changed(created, old_data, new_data, obj=None):
                if flag is true, then it means the record is changed
                you can change new_data, and the new_data will be saved to database
        """
        _saved = False
        created = False
        d = self._get_data()
        #fix when d is empty, orm will not insert record bug 2013/04/07
        if d or not self.id or insert:
            if not self.id or insert:
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
                    obj = do_(self.table.insert().values(**d), connection or self.get_connection())
                    _saved = True
                    
                setattr(self, 'id', obj.inserted_primary_key[0])
                
                if _manytomany:
                    for k, v in _manytomany.items():
                        if v:
                            _saved = getattr(self, k).update(v) or _saved
                
            else:
                _id = d.pop('id')
                if d:
                    old = d.copy()
                    if get_dispatch_send() and self.__dispatch_enabled__:
                        dispatch.call(self.__class__, 'pre_save', instance=self, created=False, data=d, old_data=self._old_values, signal=self.tablename)

                    #process auto_now
                    _manytomany = {}
                    for k, v in self.properties.items():
                        if v.property_type == 'compound' or k == 'id':
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
                        if callable(changed):
                            changed(self, created, self._old_values, d)
                            old.update(d)
                        do_(self.table.update(self.table.c.id == self.id).values(**d), connection or self.get_connection())
                        _saved = True
                        
                    if _manytomany:
                        for k, v in _manytomany.items():
                            if v is not None:
                                _saved = getattr(self, k).update(v) or _saved
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
    
    save = put
    
    def delete(self, manytomany=True, connection=None, delete_fieldname=None, send_dispatch=True):
        """
        Delete current obj
        :param manytomany: if also delete all manytomany relationships
        :param delete_fieldname: if True then it'll use 'deleted', others will 
        be the property name
        """
        if get_dispatch_send() and self.__dispatch_enabled__:
            dispatch.call(self.__class__, 'pre_delete', instance=self, signal=self.tablename)
        if manytomany:
            for k, v in self._manytomany.iteritems():
                getattr(self, k).clear()
        if delete_fieldname:
            if delete_fieldname is True:
                delete_fieldname = 'deleted'
            if not hasattr(self, delete_fieldname):
                raise KeyError("There is no %s property exists" % delete_fieldname)
            setattr(self, delete_fieldname, True)
            self.save()
        else:
            do_(self.table.delete(self.table.c.id==self.id), connection or self.get_connection())
            self.id = None
            self._old_values = {}
        if send_dispatch and get_dispatch_send() and self.__dispatch_enabled__:
            dispatch.call(self.__class__, 'post_delete', instance=self, signal=self.tablename)
            
    def __repr__(self):
        s = []
        for k, v in self._fields_list:
            if not isinstance(v, ManyToMany):
                t = getattr(self, k, None)
                if isinstance(v, Reference) and t:
                    s.append('%r:<%s:%d>' % (k, v.__class__.__name__, t.id))
                else:
                    s.append('%r:%r' % (k, t))
        return ('<%s {' % self.__class__.__name__) + ','.join(s) + '}>'
    
    def __str__(self):
        return str(self.id)
    
    def __unicode__(self):
        return str(self.id)
    
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
    def get_collection_name(cls, collection_name=None, prefix=None):
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
                collection_name = prefix + '_set_' + str(cls.__collection_set_id__)
                cls.__collection_set_id__ += 1
        else:
            if hasattr(cls, collection_name):
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
        reversed_manytomany_fieldname=None,
        **kwargs):
        prop = ManyToMany(reference_class=model, 
            collection_name=collection_name,
            reference_fieldname=reference_fieldname,
            reversed_fieldname=reversed_fieldname,
            through=through,
            through_reference_fieldname=through_reference_fieldname,
            through_reversed_fieldname=through_reversed_fieldname,
            reversed_manytomany_fieldname=reversed_manytomany_fieldname,
            **kwargs)
        cls.add_property(name, prop)
        #create property, it'll create Table object
        prop.create(cls)
        #create real table
        engine = get_connection(engine_name=cls.get_connection())
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
    def get_connection(cls):
        if cls.__connection__:
            return cls.__connection__
        return cls.get_engine_name()
        
    @classmethod
    def get_engine_name(cls):
        m = __models__.get(cls.__alias__, {})
        m1 = __model_paths__.get(cls.__module__ + '.' + cls.__name__, None)
        engine_name = cls.__engine_name__ or m.get('engine_name') or m1 or 'default'
        if not isinstance(engine_name, (str, unicode)):
            raise BadValueError('engine name should be string type, but %r found' % engine_name)
        return engine_name
    
    @classmethod
    def connect(cls, ec):
        """
        Engine name or connection object
        """
        if isinstance(ec, (str, unicode)):
            cls.__engine_name__ = ec
        else:
            cls.__connection__ = ec
        return cls
    
    @classmethod
    def bind(cls, metadata=None, auto_create=False):
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

                for k, f in cls._fields_list:
                    c = f.create(cls)
                    if c is not None:
                        cols.append(c)
                        
                #check the model_path
                model_path = cls.__module__ + '.' + cls.__name__
                _path = __models__.get(cls.tablename, {}).get('model_path', '')
                if _path and model_path != _path:
                    return
                
                #check if the table is already existed
                t = cls.metadata.tables.get(cls.tablename, None)
                if t is not None and not __auto_set_model__:
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
                        set_model(cls, created=True, engine_name=cls.__engine_name__)
                    else:
                        set_model(cls, engine_name=cls.__engine_name__)
                else:
                    if __auto_set_model__:
                        set_model(cls, engine_name=cls.__engine_name__)
        finally:
            cls._lock.release()
            
    @classmethod
    def create(cls, engine=None):
        cls._c_lock.acquire()
        try:
            engine = engine or get_connection(engine_name=cls.get_connection())
            if not cls.table.exists(engine):
                cls.table.create(engine, checkfirst=True)
            for x in cls.manytomany:
                if not x.exists(engine):
                    x.create(engine, checkfirst=True)
        finally:
            cls._c_lock.release()
            
    @classmethod
    def get(cls, condition=None, connection=None, fields=None, many_fields=None, **kwargs):
        """
        Get object from Model, if given fields, then only fields will be loaded
        into object, other properties will be Lazy
        """
        
        if condition is None:
            return None
        if isinstance(condition, (int, long)):
            _cond = cls.c.id==condition
        else:
            _cond = condition
            
        #if there is no cached object, then just fetch from database
        result = cls.connect(connection).filter(_cond, **kwargs).fields(*(fields or []))
        result.run(1)
        if not result.result:
            return
        
        #add many_fields process
        obj = None
        r = result.result.fetchone()
        if r:
            obj = cls.load(r.items(), set_saved=False)
            
            if many_fields:
                for f in many_fields:
                    if isinstance(f, (str, unicode)):
                        f_name = '_' + f + '_'
                    elif isinstance(f, Property):
                        f_name = '_' + f.property_name + '_'
                    else:
                        raise BadValueError("many_fields needs property name or instance, but %r found" % f)
                    getattr(obj, f_name, None)
            obj.set_saved()
        return obj
    
    @classmethod
    def get_or_notfound(cls, condition=None, connection=None, fields=None, many_fields=None):
        obj = cls.get(condition, connection, fields=fields, many_fields=many_fields)
        if not obj:
            raise NotFound("Can't found the object", cls, condition)
        return obj
    
    @classmethod
    def get_cached(cls, id=None, connection=None, fields=None, **kwargs):
        if id is None:
            return None
        
        _cond = cls.c.id==id
        #send 'get_object' topic to get cached object
        obj = dispatch.get(cls, 'get_object', cls.tablename, id)
        if obj:
            return obj
        #if there is no cached object, then just fetch from database
        obj = cls.connect(connection).filter(_cond, **kwargs).one()
        #send 'set_object' topic to stored the object to cache
        if obj:
            dispatch.call(cls, 'set_object', cls.tablename, instance=obj, fields=fields)
        return obj

    def push_cached(self, fields=None):
        """
        Save object to cache
        """
        dispatch.call(self.__class__, 'set_object', self.tablename, instance=self, fields=fields)
        
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
    def filter(cls, *condition, **kwargs):
        return Result(cls, **kwargs).filter(*condition)
            
    @classonlymethod
    def remove(cls, condition=None, connection=None, **kwargs):
        if isinstance(condition, (int, long)):
            condition = cls.c.id==condition
        elif isinstance(condition, (tuple, list)):
            condition = cls.c.id.in_(condition)
        do_(cls.table.delete(condition, **kwargs), connection or cls.get_connection())
            
    @classmethod
    def count(cls, condition=None, connection=None, **kwargs):
        count = do_(cls.table.count(condition, **kwargs), connection or cls.get_connection()).scalar()
        return count
            
    @classmethod
    def load(cls, values, set_saved=True):
        if isinstance(values, (list, tuple)):
            d = cls._data_prepare(values)
        elif isinstance(values, dict):
            d = values
        else:
            raise BadValueError("Can't support the data type %r" % values)
        
        if 'id' not in d or not d['id']:
            raise BadValueError("ID property must be existed or could not be empty.")
        
        o = cls()
        o._load(d, use_delay=True)
        if set_saved:
            o.set_saved()
        return o
    
    def refresh(self, fields=None, connection=None, **kwargs):
        """
        Re get the instance of current id
        """
        cond = self.c.id==self.id
        query = self.connect(connection).filter(cond, **kwargs)
        if not fields:
            fields = list(self.table.c)
        
        v = query.values_one(*fields)
        if not v:
            raise NotFound('Instance <%s:%d> can not be found' % (self.tablename, self.id))
        
        d = self._data_prepare(v.items())
        self.update(**d)
        self.set_saved()
        
    def _load(self, data, use_delay=False):
        if not data:
            return
        
        #compounds fields will be processed in the end
        compounds = []
        for prop in self.properties.values():
            if prop.name in data:
                if prop.property_type == 'compound':
                    compounds.append(prop)
                    continue
                value = data[prop.name]
            else:
                if prop.property_type == 'compound':
                    continue
                if use_delay or isinstance(prop, ManyToMany):
                    value = Lazy
                else:
                    value = prop.default_value()
            prop.__set__(self, value)
        
        for prop in compounds:
            if prop.name in data:
                value = data[prop.name]
                prop.__set__(self, value)
        
    def dump(self, fields=None):
        """
        Dump current object to dict, but the value is string
        """
        d = {}
        fields = fields or []
        if not isinstance(fields, (tuple, list)):
            fields = [fields]
        if fields and 'id' not in fields:
            fields = list(fields)
            fields.append('id')
        for k, v in self.properties.items():
            if fields and not k in fields:
                continue
            if not isinstance(v, ManyToMany):
                t = v.get_value_for_datastore(self)
                if isinstance(t, Model):
                    t = t.id
                d[k] = v.to_unicode(t)
        return d
        
#    def get_delay_field(self, name, default=None):
#        v = getattr(self, name, default)
#        if v is Lazy:
#            _id = self.id
#            if not _id:
#                raise BadValueError('Instance is not a validate object of Model %s, ID property is not found' % model_class.__name__)
#            self.refresh()
#            v = getattr(self, name, default)
#        return v
#    
    def get_cached_reference(self, fieldname, connection=None):
        prop = self.properties[fieldname]
        if not isinstance(prop, ReferenceProperty):
            raise BadPropertyTypeError("Property %s is not instance of RefernceProperty" % fieldname)
        
        reference_id = getattr(self, fieldname, None)
        if reference_id is not None:
            #this will cache the reference object
            resolved = getattr(self, prop._resolved_attr_name())
            if resolved is not None:
                return resolved
            else:
                instance = prop.reference_class.get_cached(reference_id, connection=connection)
                if instance is None:
                    raise NotFound('ReferenceProperty %s failed to be resolved' % self.reference_fieldname, self.reference_class, reference_id)
                setattr(model_instance, self._resolved_attr_name(), instance)
                return instance
        else:
            return None

