# This module is used for wrapping SqlAlchemy to a simple ORM
# Author: limodou <limodou@gmail.com>
# 2008.06.11
# Update:
#   2010.4.1 Add get() support to Result and ManyResult


__all__ = ['Field', 'get_connection', 'Model', 'create_all',
    'set_debug_query', 'set_auto_create', 'set_connection', 'get_model',
    'CHAR', 'BLOB', 'TEXT', 'DECIMAL', 'Index', 'datetime', 'decimal',
    'PICKLE', 
    'BlobProperty', 'BooleanProperty', 'DateProperty', 'DateTimeProperty',
    'TimeProperty', 'DecimalProperty', 'FloatProperty', 'SQLStorage',
    'IntegerProperty', 'Property', 'StringProperty', 'CharProperty',
    'TextProperty', 'UnicodeProperty', 'Reference', 'ReferenceProperty',
    'PickleType',
    'SelfReference', 'SelfReferenceProperty', 'OneToOne', 'ManyToMany',
    'ReservedWordError', 'BadValueError', 'DuplicatePropertyError', 
    'ModelInstanceError', 'KindError', 'ConfigurationError',
    'BadPropertyTypeError', 'FILE', 'Begin', 'Commit', 'Rollback']

__default_connection__ = None  #global connection instance
__auto_create__ = True
__debug_query__ = None
__default_encoding__ = 'utf-8'
__zero_float__ = 0.0000005

import decimal
import threading
import datetime
from uliweb.utils import date
from sqlalchemy import *
from sqlalchemy.sql import select, ColumnElement
from uliweb.core import dispatch
import threading

Local = threading.local()
Local.dispatch_send = True
Local.conn = None

_default_metadata = MetaData()

class Error(Exception):pass
class NotFound(Error):pass
class ReservedWordError(Error):pass
class ModelInstanceError(Error):pass
class DuplicatePropertyError(Error):
  """Raised when a property is duplicated in a model definition."""
class BadValueError(Error):pass
class BadPropertyTypeError(Error):pass
class KindError(Error):pass
class ConfigurationError(Error):pass

_SELF_REFERENCE = object()

def set_auto_create(flag):
    global __auto_create__
    __auto_create__ = flag
    
def set_debug_query(flag):
    global __debug_query__
    __debug_query__ = flag
    
def set_encoding(encoding):
    global __default_encoding__
    __default_encoding__ = encoding
    
def set_dispatch_send(flag):
    global Local
    Local.dispatch_send = flag
    
def get_dispatch_send(default=True):
    global Local
    if not hasattr(Local, 'dispatch_send'):
        Local.dispatch_send = default
    return Local.dispatch_send

def get_connection(connection='', metadata=_default_metadata, default=True, debug=None, **args):
    """
    default encoding is utf-8
    """
    global __default_connection__
  
    debug = debug or __debug_query__
    
    if default and __default_connection__:
        return __default_connection__
    
    if 'strategy' not in args:
        args['strategy'] = 'threadlocal'
        
    if isinstance(connection, (str, unicode)):
        db = create_engine(connection, **args)
    else:
        db = connection
        
    if default:
        __default_connection__ = db
        
    if debug:
        db.echo = debug
        
    if not metadata:
        metadata = MetaData(db)
    else:
        metadata.bind = db
        
    db.metadata = metadata
    create_all(db)
    return db

def set_connection(db, default=True, debug=False):
    global __default_connection__

    if default:
        __default_connection__ = db
    if debug:
        db.echo = debug
    metadata = MetaData(db)
    db.metadata = metadata
    
def do_(query):
    """
    Execute a query
    """
    if hasattr(Local, 'conn') and Local.conn:
        conn = Local.conn
    else:
        conn = get_connection()
    return conn.execute(query)
    
def Begin(db=None, create=False):
    if hasattr(Local, 'trans') and Local.trans:
        return
    if not db:
        db = get_connection()
    if create:
        Local.conn = conn = db.connect()
        Local.trans = conn.begin()
    else:
        db.begin()
    
def Commit(db=None, close=False):
    """
    Before using this function, you should called Begin first.
    """
    if hasattr(Local, 'trans') and Local.trans:
        try:
            Local.trans.commit()
        finally:
            Local.trans = None
            if close:
                Local.conn.close()
                Local.conn = None
    else:
        if not db:
            db = get_connection()
        conn = db.contextual_connect()
        if conn.in_transaction():
            db.commit()
        if close:
            conn.close()

def Rollback(db=None, close=False):
    """
    Before using this function, you should called Begin first.
    """
    if hasattr(Local, 'trans') and Local.trans:
        try:
            Local.trans.rollback()
        finally:
            Local.trans = None
            if close:
                Local.conn.close()
                Local.conn = None
    else:
        if not db:
            db = get_connection()
        conn = db.contextual_connect()
        if conn.in_transaction():
            db.rollback()
        if close:
            conn.close()
    
            
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

def check_reserved_word(f):
    if f in ['put', 'save', 'table', 'tablename'] or f in dir(Model):
        raise ReservedWordError(
            "Cannot define property using reserved word '%s'. " % f
            )

__models__ = {}

def create_all(db=None):
    global __models__
    for cls in __models__.values():
        if not cls['created'] and cls['model']:
            cls['model'].bind(db.metadata, auto_create=__auto_create__)
            cls['created'] = True
        
def set_model(model, tablename=None, created=None):
    """
    Register an model and tablename to a global variable.
    model could be a string format, i.e., 'uliweb.contrib.auth.models.User'
    """
    global __models__
    if isinstance(model, type) and issubclass(model, Model):
        tablename = model.tablename
    item = __models__.setdefault(tablename, {})
    if created is not None:
        item['created'] = created
    else:
        item['created'] = None
    if isinstance(model, (str, unicode)):
        model_name = model
        appname = model.rsplit('.', 2)[0]
        #for example 'uliweb.contrib.auth.models.User'
        model = None
    else:
        model_name = ''
        appname = model.__module__.rsplit('.', 1)[0]
        #for example 'uliweb.contrib.auth.models'
        
    item['model'] = model
    item['model_name'] = model_name
    item['appname'] = appname
    
def get_model(model):
    """
    Return a real model object, so if the model is already a Model class, then
    return it directly. If not then import it.
    """
    global __models__
    if model is _SELF_REFERENCE:
        return model
    if isinstance(model, type) and issubclass(model, Model):
        return model
    if model in __models__:
        item = __models__[model]
        m = item['model']
        if isinstance(m, type)  and issubclass(m, Model):
            return m
        else:
            m, name = item['model_name'].rsplit('.', 1)
            mod = __import__(m, {}, {}, [''])
            model = getattr(mod, name)
            item['model'] = model
            return model
    else:
        raise Error("Can't found the model %s" % model)
    
def valid_model(model):
    global __models__
    if isinstance(model, type) and issubclass(model, Model):
        return True
    return model in __models__

class ModelMetaclass(type):
    def __init__(cls, name, bases, dct):
        super(ModelMetaclass, cls).__init__(name, bases, dct)
        if name == 'Model':
            return
        cls._set_tablename()
        
        cls.properties = {}
        defined = set()
        for base in bases:
            if hasattr(base, 'properties'):
                property_keys = base.properties.keys()
                duplicate_properties = defined.intersection(property_keys)
                if duplicate_properties:
                    raise DuplicatePropertyError(
                        'Duplicate properties in base class %s already defined: %s' %
                        (base.__name__, list(duplicate_properties)))
                defined.update(property_keys)
                cls.properties.update(base.properties)
        
        cls._manytomany = {}
        for attr_name in dct.keys():
            attr = dct[attr_name]
            if isinstance(attr, Property):
                check_reserved_word(attr_name)
                if attr_name in defined:
                    raise DuplicatePropertyError('Duplicate property: %s' % attr_name)
                defined.add(attr_name)
                cls.properties[attr_name] = attr
                attr.__property_config__(cls, attr_name)
                
                if isinstance(attr, ManyToMany):
                    cls._manytomany[attr_name] = attr
                
        #if there is already defined primary_key, the id will not be primary_key
        has_primary_key = bool([v for v in cls.properties.itervalues() if 'primary_key' in v.kwargs])
        
        #add __without_id__ attribute to model, if set it, uliorm will not
        #create 'id' field for the model
        without_id = getattr(cls, '__without_id__', False)
        if 'id' not in cls.properties and not without_id:
            cls.properties['id'] = f = Field(int, autoincrement=True, 
                primary_key=not has_primary_key, default=None)
            f.__property_config__(cls, 'id')
            setattr(cls, 'id', f)

#        fields_list = [(k, v) for k, v in cls.properties.items() if not isinstance(v, ManyToMany)]
        fields_list = [(k, v) for k, v in cls.properties.items()]
        fields_list.sort(lambda x, y: cmp(x[1].creation_counter, y[1].creation_counter))
        cls._fields_list = fields_list
        
        cls.bind(auto_create=__auto_create__)
        
class Property(object):
    data_type = str
    field_class = String
    creation_counter = 0

    def __init__(self, verbose_name=None, name=None, default=None,
        required=False, validators=None, choices=None, max_length=None, 
        hint='', auto=None, auto_add=None, type_class=None, type_attrs=None, **kwargs):
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
        self.creation_counter = Property.creation_counter
        self.value = None
        self.type_attrs = type_attrs or {}
        self.type_class = type_class or self.field_class
        Property.creation_counter += 1
        
    def create(self, cls):
        args = self.kwargs.copy()
        args['key'] = self.name
#        if callable(self.default):
#            args['default'] = self.default()
        args['default'] = self.default
        args['primary_key'] = self.kwargs.get('primary_key', False)
        args['autoincrement'] = self.kwargs.get('autoincrement', False)
        args['index'] = self.kwargs.get('index', False)
        args['unique'] = self.kwargs.get('unique', False)
        args['nullable'] = self.kwargs.get('nullable', True)
        f_type = self._create_type()
        return Column(self.property_name, f_type, **args)

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

    def __get__(self, model_instance, model_class):
        if model_instance is None:
            return self

        try:
            return getattr(model_instance, self._attr_name())
        except AttributeError:
            return None
        
    def __set__(self, model_instance, value):
        if model_instance is None:
            return
        
        value = self.validate(value)
        #add value to model_instance._changed_value, so that you can test if
        #a object really need to save
        setattr(model_instance, self._attr_name(), value)

#    def default_value(self, model_instance=None):
#        if callable(self.default):
#            return self.default(model_instance)
#        return self.default
    def default_value(self):
        if callable(self.default):
            return self.default()
        return self.default
    
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
        if value is not None:
            try:
                value = self.convert(value)
            except TypeError, err:
                raise BadValueError('Property %s must be convertible '
                    'to %s, but the value is (%s)' % (self.name, self.data_type, err))
        
        for v in self.validators:
            v(value)
        return value

    def empty(self, value):
        return value is None

    def get_value_for_datastore(self, model_instance):
        return self.__get__(model_instance, model_instance.__class__)

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
        return '_' + self.name + '_'
    
    def to_str(self, v):
        if isinstance(v, unicode):
            return v.encode(__default_encoding__)
        elif isinstance(v, str):
            return v
        else:
            return str(v)
        
    def to_unicode(self, v):
        if isinstance(v, str):
            return unicode(v, __default_encoding__)
        elif isinstance(v, unicode):
            return v
        else:
            return unicode(v)
    
class CharProperty(Property):
    data_type = unicode
    field_class = CHAR
    
    def __init__(self, verbose_name=None, default=u'', max_length=30, **kwds):
        super(CharProperty, self).__init__(verbose_name, default=default, max_length=max_length, **kwds)
    
    def empty(self, value):
        return not value
    
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
    def __init__(self, verbose_name=None, default='', max_length=255, **kwds):
        super(FileProperty, self).__init__(verbose_name, default=default, max_length=max_length, **kwds)
        
class UnicodeProperty(CharProperty):
    field_class = Unicode
    
class TextProperty(StringProperty):
    field_class = Text
    
    def __init__(self, verbose_name=None, default='', **kwds):
        super(TextProperty, self).__init__(verbose_name, default=default, max_length=None, **kwds)
    
class BlobProperty(StringProperty):
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
    
    def __init__(self, verbose_name=None, default='', **kwds):
        super(PickleProperty, self).__init__(verbose_name, default=default, **kwds)

    def convert(self, value):
        return value
    
    def validate(self, value):
        return value
    
class DateTimeProperty(Property):
    data_type = datetime.datetime
    field_class = DateTime
    
    def __init__(self, verbose_name=None, auto_now=False, auto_now_add=False,
            format=None, **kwds):
        super(DateTimeProperty, self).__init__(verbose_name, auto=auto_now, auto_add=auto_now_add, **kwds)
        self.auto_now = auto_now
        self.auto_now_add = auto_now_add
        self.format = format

    def validate(self, value):
        value = super(DateTimeProperty, self).validate(value)
        if value and not isinstance(value, self.data_type):
            raise BadValueError('Property %s must be a %s' %
                (self.name, self.data_type.__name__))
        return value
    
    @staticmethod
    def now():
        return date.now()

    def convert(self, value):
        if not value:
            return None
        d = date.to_datetime(value, format=self.format)
        if d:
            return d
        raise BadValueError('The datetime value is not a valid format')
    
    def to_str(self, v):
        if isinstance(v, datetime.datetime):
            return v.strftime('%Y-%m-%d %H:%M:%S')
        else:
            return str(v)
    
    def to_unicode(self, v):
        if isinstance(v, datetime.datetime):
            return unicode(v.strftime(u'%Y-%m-%d %H:%M:%S'))
        else:
            return unicode(v)

class DateProperty(DateTimeProperty):
    data_type = datetime.date
    field_class = Date
    
    #if the value is datetime.datetime, this convert will not be invoked at all
    #Todo: so if I need to fix it?
    #this is fixed by call date.to_date(value) in validate() method
#    def validate(self, value):
#        value = super(DateProperty, self).validate(value)
#        if value:
#            return date.to_date(value)
#        return value

    def make_value_from_datastore(self, value):
        if value is not None:
            value = date.to_date(value)
        return value

    def convert(self, value):
        if not value:
            return None
        d = date.to_date(value, format=self.format)
        if d:
            return d
        raise BadValueError('The date value is not a valid format')
    
    def to_str(self, v):
        if isinstance(v, datetime.date):
            return v.strftime('%Y-%m-%d')
        else:
            return str(v)
        
    def to_unicode(self, v):
        if isinstance(v, datetime.date):
            return unicode(v.strftime('%Y-%m-%d'))
        else:
            return unicode(v)

class TimeProperty(DateTimeProperty):
    """A time property, which stores a time without a date."""

    data_type = datetime.time
    field_class = Time
    
    def make_value_from_datastore(self, value):
        if value is not None:
            value = date.to_time(value)
        return value

    def convert(self, value):
        if not value:
            return None
        d = date.to_time(value, format=self.format)
        if d:
            return d
        raise BadValueError('The time value is not a valid format')
    
    def to_str(self, v):
        if isinstance(v, datetime.time):
            return v.strftime('%H:%M:%S')
        else:
            return str(v)

    def to_unicode(self, v):
        if isinstance(v, datetime.time):
            return unicode(v.strftime('%H:%M:%S'))
        else:
            return unicode(v)

class IntegerProperty(Property):
    """An integer property."""

    data_type = int
    field_class = Integer
    
    def __init__(self, verbose_name=None, default=0, **kwds):
        super(IntegerProperty, self).__init__(verbose_name, default=default, **kwds)
    
    def validate(self, value):
        value = super(IntegerProperty, self).validate(value)
        if value and not isinstance(value, (int, long, bool)):
            raise BadValueError('Property %s must be an int, long or bool, not a %s'
                % (self.name, type(value).__name__))
        return value

class FloatProperty(Property):
    """A float property."""

    data_type = float
    field_class = Float
    
    def __init__(self, verbose_name=None, default=0.0, precision=None, **kwds):
        super(FloatProperty, self).__init__(verbose_name, default=default, **kwds)
        self.precision = precision
        
    def _create_type(self):
        f_type = self.type_class(precision=self.precision, **self.type_attrs)
        return f_type
    
    def validate(self, value):
        value = super(FloatProperty, self).validate(value)
        if value is not None and not isinstance(value, float):
            raise BadValueError('Property %s must be a float, not a %s' 
                % (self.name, type(value).__name__))
        if abs(value) < __zero_float__:
            value = 0.0
        return value
    
class DecimalProperty(Property):
    """A float property."""

    data_type = decimal.Decimal
    field_class = Numeric
    
    def __init__(self, verbose_name=None, default='0.0', precision=None, scale=None, **kwds):
        super(DecimalProperty, self).__init__(verbose_name, default=default, **kwds)
        self.precision = precision
        self.scale = scale
   
    def validate(self, value):
        value = super(DecimalProperty, self).validate(value)
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
    
    def __init__(self, verbose_name=None, default=False, **kwds):
        super(BooleanProperty, self).__init__(verbose_name, default=default, **kwds)
    
    def validate(self, value):
        value = super(BooleanProperty, self).validate(value)
        if value is not None and not isinstance(value, bool):
            raise BadValueError('Property %s must be a boolean, not a %s' 
                % (self.name, type(value).__name__))
        return value

class ReferenceProperty(Property):
    """A property that represents a many-to-one reference to another model.
    """
    field_class = Integer

    def __init__(self, reference_class=None, verbose_name=None, collection_name=None, 
        reference_fieldname=None, required=False, **attrs):
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

        self.collection_name = collection_name
        self.reference_fieldname = reference_fieldname or 'id'
        self.required = required

        if reference_class is None:
            reference_class = Model
            
        if not (
                (isinstance(reference_class, type) and issubclass(reference_class, Model)) or
                reference_class is _SELF_REFERENCE or
                valid_model(reference_class)):
            raise KindError('reference_class must be Model or _SELF_REFERENCE or available table name')
        self.reference_class = self.data_type = get_model(reference_class)
        
    def create(self, cls):
        args = self.kwargs.copy()
        args['key'] = self.name
#        if not callable(self.default):
        args['default'] = self.default
        args['primary_key'] = self.kwargs.get('primary_key', False)
        args['autoincrement'] = self.kwargs.get('autoincrement', False)
        args['index'] = self.kwargs.get('index', False)
        args['unique'] = self.kwargs.get('unique', False)
        args['nullable'] = self.kwargs.get('nullable', True)
        f_type = self._create_type()
#        return Column(self.property_name, f_type, ForeignKey("%s.id" % self.reference_class.tablename), **args)
        return Column(self.property_name, f_type, **args)
    
    def _create_type(self):
        if not hasattr(self.reference_class, self.reference_fieldname):
            raise KindError('reference_fieldname is not existed')
        self.reference_field = getattr(self.reference_class, self.reference_fieldname)
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

        if self.reference_class is _SELF_REFERENCE:
            self.reference_class = self.data_type = model_class

        if self.collection_name is None:
            self.collection_name = '%s_set' % (model_class.tablename)
        if hasattr(self.reference_class, self.collection_name):
            raise DuplicatePropertyError('Class %s already has property %s'
                 % (self.reference_class.__name__, self.collection_name))
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
            reference_id = getattr(model_instance, self._attr_name())
        else:
            reference_id = None
        if reference_id is not None:
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
                    raise NotFound('ReferenceProperty %s failed to be resolved' % self.reference_fieldname)
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
            return value

        if value is not None and not value.is_saved():
            raise BadValueError(
                    '%s instance must be saved before it can be stored as a '
                    'reference' % self.reference_class.__class__.__name__)

        value = super(ReferenceProperty, self).validate(value)

        if value is not None and not isinstance(value, self.reference_class):
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
        args = self.kwargs.copy()
        args['key'] = self.name
#        if not callable(self.default):
        args['default'] = self.default
        args['primary_key'] = self.kwargs.get('primary_key', False)
        args['autoincrement'] = self.kwargs.get('autoincrement', False)
        args['index'] = self.kwargs.get('index', False)
        args['unique'] = self.kwargs.get('unique', True)
        args['nullable'] = self.kwargs.get('nullable', True)
        f_type = self._create_type()
#        return Column(self.property_name, f_type, ForeignKey("%s.id" % self.reference_class.tablename), **args)
        return Column(self.property_name, f_type, **args)

    def __property_config__(self, model_class, property_name):
        """Loads all of the references that point to this model.
        """
        super(ReferenceProperty, self).__property_config__(model_class, property_name)
    
        if self.reference_class is _SELF_REFERENCE:
            self.reference_class = self.data_type = model_class
    
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
        self.columns = [self.model.table]
        self.funcs = []
        self.args = args
        self.kwargs = kwargs
        self.result = None
        
    def all(self):
        return self
    
    def get(self, condition=None):
        if isinstance(condition, (int, long)):
            return self.filter(self.model.c.id==condition).one()
        else:
            return self.filter(condition).one()
    
    def count(self):
        return self.model.count(self.condition)

    def filter(self, condition):
        if condition is None:
            return self
        if self.condition is not None:
            self.condition = condition & self.condition
        else:
            self.condition = condition
        return self
    
    def order_by(self, *args, **kwargs):
        self.funcs.append(('order_by', args, kwargs))
        return self
    
    def values(self, *args, **kwargs):
        self.funcs.append(('with_only_columns', (args,), kwargs))
        r = self.run()
        while 1:
            x = r.fetchone()
            if x:
                yield x
            else:
                raise StopIteration
    
    def values_one(self, *args, **kwargs):
        self.funcs.append(('with_only_columns', (args,), kwargs))
        self.run(1)
        result = self.result.fetchone()
        return result

    def distinct(self, *args, **kwargs):
        self.funcs.append(('distinct', args, kwargs))
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
            self.result = do_(self.model.table.update().where(self.condition).values(**kwargs))
        else:
            self.result = do_(self.model.table.update().values(**kwargs))
        return self.result
    
    def run(self, limit=0):
        if self.condition is not None:
            query = select(self.columns, self.condition)
        else:
            query = select(self.columns)
        for func, args, kwargs in self.funcs:
            query = getattr(query, func)(*args, **kwargs)
        #add limit support
        if limit > 0:
            query = getattr(query, 'limit')(limit)
        self.result = do_(query)
        return self.result
    
    def one(self):
        self.run(1)
        if not self.result:
            return
        
        result = self.result.fetchone()
        if result:
            d = self.model._data_prepare(result.items())
            o = self.model(**d)
            o.set_saved()
            return o
    
    def clear(self):
        if self.condition is None:
            return
        return self.model.remove(self.condition)
    
    remove = clear
            
    def __del__(self):
        if self.result:
            self.result.close()

    def __iter__(self):
        self.result = self.run()
        while 1:
            result = self.result.fetchone()
            if not result:
                raise StopIteration
            d = self.model._data_prepare(result.items())
            o = self.model(**d)
            o.set_saved()
            yield o
  
class ReverseResult(Result):
    def __init__(self, model, condition, a_field, b_table, instance, b_field, *args, **kwargs):
        self.model = model
        self.b_table = b_table
        self.b_field = b_field
        self.instance = instance
        self.condition = condition
        self.a_field = a_field
        self.columns = [self.model.table]
        self.funcs = []
        self.args = args
        self.kwargs = kwargs
        self.result = None
        
    def has(self, *objs):
        ids = get_objs_columns(objs)
        
        if not ids:
            return False
        
        count = do_(self.model.table.count(self.condition & (self.model.table.c['id'].in_(ids)))).scalar()
        return count > 0
    
    def ids(self):
        query = select([self.model.c['id']], self.condition)
        ids = [x[0] for x in do_(query)]
        return ids
    
    def clear(self, *objs):
        """
        Clear the third relationship table, but not the ModelA or ModelB
        """
        if objs:
            ids = get_objs_columns(objs)
            do_(self.model.table.delete(self.condition & self.model.table.c['id'].in_(ids)))
        else:
            do_(self.model.table.delete(self.condition))
    
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
        self.columns = [self.modelb.table]
        self.condition = None
        self.funcs = []
        self.result = None
        self.with_relation_name = None
        self.through_model = through_model
        
    def get(self, condition=None):
        if not isinstance(condition, ColumnElement):
            return self.filter(self.modelb.c[self.realfieldb]==condition).one()
        else:
            return self.filter(condition).one()

    def add(self, *objs):
        new_objs = []
        for x in objs:
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
                do_(self.table.insert().values(**d))
                modified = modified or True
        return modified
         
    def ids(self):
        query = select([self.table.c[self.fieldb]], self.table.c[self.fielda]==self.valuea)
        ids = [x[0] for x in do_(query)]
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
                do_(self.table.insert().values(**d))
                modified = True
                
        if ids: #if there are still ids, so delete them
            self.clear(*ids)
            modified = True
        return modified
            
    def clear(self, *objs):
        """
        Clear the third relationship table, but not the ModelA or ModelB
        """
        if objs:
            ids = get_objs_columns(objs, self.realfieldb)
            do_(self.table.delete((self.table.c[self.fielda]==self.valuea) & (self.table.c[self.fieldb].in_(ids))))
        else:
            do_(self.table.delete(self.table.c[self.fielda]==self.valuea))
       
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
        
        count = do_(self.table.count((self.table.c[self.fielda]==self.valuea) & (self.table.c[self.fieldb].in_(ids)))).scalar()
        return count > 0
        
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
        if self.with_relation_name:
            columns = [self.table] + self.columns
        else:
            columns = self.columns
        query = select(columns, (self.table.c[self.fielda] == self.valuea) & (self.table.c[self.fieldb] == self.modelb.c[self.realfieldb]) & self.condition)
        for func, args, kwargs in self.funcs:
            query = getattr(query, func)(*args, **kwargs)
        if limit > 0:
            query = getattr(query, 'limit')(limit)
        self.result = do_(query)
        return self.result
        
    def one(self):
        self.run(1)
        if not self.result:
            return
        result = self.result.fetchone()
        if result:
            offset = 0
            if self.with_relation_name:
                offset = len(self.table.columns)
                
            d = self.modelb._data_prepare(zip(result.keys()[offset:], result.values()[offset:]))
            o = self.modelb(**d)
            o.set_saved()
            
            if self.with_relation_name:
                d_ = self.through_model._data_prepare(zip(result.keys()[:offset], result.values()[:offset]))
                r = self.through_model(**d_)
                r.set_saved()
                setattr(o, self.with_relation_name, r)
                
            return o

    def __del__(self):
        if self.result:
            self.result.close()
    
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
           
            d = self.modelb._data_prepare(zip(result.keys()[offset:], result.values()[offset:]))
            o = self.modelb(**d)
            o.set_saved()
            
            if self.with_relation_name:
                d_ = self.through_model._data_prepare(zip(result.keys()[:offset], result.values()[:offset]))
                r = self.through_model(**d_)
                r.set_saved()
                setattr(o, self.with_relation_name, r)
                
            yield o
        
class ManyToMany(ReferenceProperty):
    def __init__(self, reference_class=None, verbose_name=None, collection_name=None, 
        reference_fieldname=None, reversed_fieldname=None, required=False, through=None, **attrs):
            
        super(ManyToMany, self).__init__(reference_class=reference_class,
            verbose_name=verbose_name, collection_name=collection_name, 
            reference_fieldname=reference_fieldname, required=required, **attrs)
    
        self.reversed_fieldname = reversed_fieldname or 'id'
        self.through = through

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
            self.fieldb = "%s_id" % self.reference_class.tablename
            self.table = self.create_table()
            #add appname to self.table
            appname = self.model_class.__module__
            if appname.endswith('.models'):
                self.table.__appname__ = appname[:-7]
            self.model_class.manytomany.append(self.table)
            Index('%s_mindx' % self.tablename, self.table.c[self.fielda], self.table.c[self.fieldb], unique=True)
    
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
                if isinstance(v, ReferenceProperty):
                    if self.model_class is v.reference_class:
                        self.fielda = k
                        self.reversed_fieldname = v.reference_fieldname
                    elif self.reference_class is v.reference_class:
                        self.fieldb = k
                        self.reference_fieldname = v.reference_fieldname
            if not hasattr(self.through, self.fielda):
                raise BadPropertyTypeError("Can't find %s in Model %r" % (self.fielda, self.through))
            if not hasattr(self.through, self.fieldb):
                raise BadPropertyTypeError("Can't find %s in Model %r" % (self.fieldb, self.through))
            self.table = self.through.table
            appname = self.model_class.__module__
            if appname.endswith('.models'):
                self.table.__appname__ = appname[:-7]
            self.model_class.manytomany.append(self.table)
            Index('%s_mindx' % self.tablename, self.table.c[self.fielda], self.table.c[self.fieldb], unique=True)
    
    def __property_config__(self, model_class, property_name):
        """Loads all of the references that point to this model.
        """
        super(ReferenceProperty, self).__property_config__(model_class, property_name)
    
        if self.reference_class is _SELF_REFERENCE:
            self.reference_class = self.data_type = model_class
        self.tablename = '%s_%s_%s' % (model_class.tablename, self.reference_class.tablename, property_name)
        if self.collection_name is None:
            self.collection_name = '%s_set' % (model_class.tablename)
        if hasattr(self.reference_class, self.collection_name):
            raise DuplicatePropertyError('Class %s already has property %s'
                 % (self.reference_class.__name__, self.collection_name))
        setattr(self.reference_class, self.collection_name,
            _ManyToManyReverseReferenceProperty(self, self.collection_name))
    
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
        
        if value:
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
            
    def filter(self, condition=None):
        sub_query = select([self.table.c[self.fielda]], (self.table.c[self.fieldb] == self.reference_class.c[self.reference_fieldname]) & condition)
        condition = self.model_class.c[self.reversed_fieldname].in_(sub_query)
        return condition
        
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
        self.collection_name = collection_name

    def __get__(self, model_instance, model_class):
        """Fetches collection of model instances of this collection property."""
        self.reference_property.init_through()
        self._reversed_id = self.reference_property.reference_fieldname
        if model_instance:
            reference_id = getattr(model_instance, self._reversed_id, None)
            x = ManyResult(self.reference_property.reference_class, model_instance,
                self.collection_name,
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

_fields_mapping = {
    str:StringProperty,
    CHAR:CharProperty,
    unicode: UnicodeProperty,
    TEXT:TextProperty,
    BLOB:BlobProperty,
    FILE:FileProperty,
    int:IntegerProperty,
    float:FloatProperty,
    bool:BooleanProperty,
    datetime.datetime:DateTimeProperty,
    datetime.date:DateProperty,
    datetime.time:TimeProperty,
    decimal.Decimal:DecimalProperty,
    DECIMAL:DecimalProperty,
    PICKLE:PickleProperty,
}
def Field(type, **kwargs):
    t = _fields_mapping.get(type, type)
    return t(**kwargs)

class Model(object):

    __metaclass__ = ModelMetaclass
    __dispatch_enabled__ = True
    
    _lock = threading.Lock()
    _c_lock = threading.Lock()
    
    def __init__(self, **kwargs):
        self._old_values = {}
        for prop in self.properties.values():
            if prop.name in kwargs:
                value = kwargs[prop.name]
            else:
                value = prop.default_value()
            prop.__set__(self, value)
        
    def set_saved(self):
        self._old_values = self.to_dict()
        for k, v in self.properties.items():
            if isinstance(v, ManyToMany):
                t = v.get_value_for_datastore(self, cached=True)
                self._old_values[k] = t
        
    def to_dict(self, fields=[], convert=True, manytomany=False):
        d = {}
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
                    d[k] = getattr(self, k).ids()
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
            return v
           
    def _get_data(self):
        """
        Get the changed property, it'll be used to save the object
        """
        if self.id is None:
            d = {}
            for k, v in self.properties.items():
                if not isinstance(v, ManyToMany):
                    x = v.get_value_for_datastore(self)
                    if isinstance(x, Model):
                        x = x.id
                else:
                    x = v.get_value_for_datastore(self, cached=True)
                if x is not None:
                    d[k] = x
        else:
            d = {}
            d['id'] = self.id
            for k, v in self.properties.items():
                t = self._old_values.get(k, None)
                if not isinstance(v, ManyToMany):
                    x = v.get_value_for_datastore(self)
                    #todo If need to support ManyToMany and Reference except id field?
                    if isinstance(x, Model):
                        
                        \
                        x = x.id
                else:
                    x = v.get_value_for_datastore(self, cached=True)
                if t != self.field_str(x):
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
            
    def put(self, insert=False):
        """
        If insert=True, then it'll use insert() indead of update()
        """
        saved = False
        created = False
        d = self._get_data()
        if d:
            if not self.id or insert:
                created = True
                old = d.copy()
                
                if get_dispatch_send() and self.__dispatch_enabled__:
                    dispatch.call(self.__class__, 'pre_save', instance=self, created=True, data=d, old_data=self._old_values)
                
                #process auto_now_add
                _manytomany = {}
                for k, v in self.properties.items():
                    if not isinstance(v, ManyToMany):
                        if isinstance(v, DateTimeProperty) and v.auto_now_add and k not in d:
                            d[k] = v.now()
                        elif (not k in d) and v.auto_add:
                            d[k] = v.default_value()
                    else:
                        if k in d:
                            _manytomany[k] = d.pop(k)
                            old.pop(k)
                if d:
                    obj = do_(self.table.insert().values(**d))
                    if old:
                        saved = True
                    
                setattr(self, 'id', obj.inserted_primary_key[0])
                
                if _manytomany:
                    for k, v in _manytomany.iteritems():
                        if v:
                            saved = getattr(self, k).update(v) or saved
                
            else:
                _id = d.pop('id')
                if d:
                    old = d.copy()
                    
                    if get_dispatch_send() and self.__dispatch_enabled__:
                        dispatch.call(self.__class__, 'pre_save', instance=self, created=False, data=d, old_data=self._old_values)

                    #process auto_now
                    _manytomany = {}
                    for k, v in self.properties.items():
                        if not isinstance(v, ManyToMany):
                            if isinstance(v, DateTimeProperty) and v.auto_now and k not in d:
                                d[k] = v.now()
                            elif (not k in d) and v.auto:
                                d[k] = v.default_value()
                        else:
                            if k in d:
                                _manytomany[k] = d.pop(k)
                                old.pop(k)
                    if d:
                        do_(self.table.update(self.table.c.id == self.id).values(**d))
                        if old:
                            saved = True
                    if _manytomany:
                        for k, v in _manytomany.iteritems():
                            if v is not None:
                                saved = getattr(self, k).update(v) or saved
            if saved:
                for k, v in d.items():
                    x = self.properties[k].get_value_for_datastore(self)
                    if self.field_str(x) != self.field_str(v):
                        setattr(self, k, v)
                if get_dispatch_send() and self.__dispatch_enabled__:
                    dispatch.call(self.__class__, 'post_save', instance=self, created=created, data=old, old_data=self._old_values)
                self.set_saved()
                
        return saved
    
    save = put
    
    def delete(self):
        if get_dispatch_send() and self.__dispatch_enabled__:
            dispatch.call(self.__class__, 'pre_delete', instance=self)
        do_(self.table.delete(self.table.c.id==self.id))
        if get_dispatch_send() and self.__dispatch_enabled__:
            dispatch.call(self.__class__, 'post_delete', instance=self)
        self.id = None
        self._old_values = {}
            
    def __repr__(self):
        s = []
        for k, v in self._fields_list:
            if not isinstance(v, ManyToMany):
                s.append('%r:%r' % (k, getattr(self, k, None)))
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
    def _set_tablename(cls, appname=None):
        if not hasattr(cls, '__tablename__'):
            name = cls.__name__.lower()
        else:
            name = cls.__tablename__
        if appname:
            name = appname.lower() + '_' + name
        cls.tablename = name
        
    @classmethod
    def bind(cls, metadata=None, auto_create=False):
        cls._lock.acquire()
        try:
            cls.metadata = metadata or _default_metadata
            if cls.metadata and not hasattr(cls, '_bound'):
                cols = []
                cls.manytomany = []
                for k, f in cls.properties.items():
                    c = f.create(cls)
                    if c is not None:
                        cols.append(c)
                        
                #if there is already a same name table, then remove the old one
                #replace with new one
                t = cls.metadata.tables.get(cls.tablename, None)
                if t is not None:
                    cls.metadata.remove(t)
                args = getattr(cls, '__table_args__', {})
                args['mysql_charset'] = 'utf8'
                cls.table = Table(cls.tablename, cls.metadata, *cols, **args)
                #add appname to self.table
                appname = cls.__module__
                if appname.endswith('.models'):
                    cls.table.__appname__ = appname[:-7]
                
                cls.c = cls.table.c
                cls.columns = cls.table.c
                
                if hasattr(cls, 'OnInit'):
                    cls.OnInit()
                
                cls._bound = True
            if cls._bound:
                if auto_create:
                    #only metadata is _default_metadata and bound 
                    #then the table will be created
                    #otherwise the creation of tables will be via: create_all(db)
                    if cls.metadata == _default_metadata and cls.metadata.bind:
                        cls.create()
                        set_model(cls, created=True)
                    else:
                        set_model(cls)
        finally:
            cls._lock.release()
            
    @classmethod
    def create(cls):
        cls._c_lock.acquire()
        try:
            if not cls.table.exists():
                cls.table.create(checkfirst=True)
            for x in cls.manytomany:
                if not x.exists():
                    x.create(checkfirst=True)
        finally:
            cls._c_lock.release()
            
    @classmethod
    def get(cls, condition=None):
        if condition is None:
            return None
        if isinstance(condition, (int, long)):
            _cond = cls.c.id==condition
        else:
            _cond = condition
        #send 'get_object' topic to get cached object
        obj = dispatch.get(cls, 'get_object', condition=_cond)
        if obj:
            return obj
        #if there is no cached object, then just fetch from database
        obj = cls.filter(_cond).one()
        #send 'set_object' topic to stored the object to cache
        if obj:
            dispatch.call(cls, 'set_object', condition=_cond, instance=obj)
        return obj
    
    @classmethod
    def get_or_notfound(cls, condition=None):
        obj = cls.get(condition)
        if not obj:
            raise NotFound, "Can't found the object"
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
    def all(cls):
        return Result(cls)
        
    @classmethod
    def filter(cls, condition=None, **kwargs):
        return Result(cls, condition, **kwargs)
            
    @classmethod
    def remove(cls, condition=None, **kwargs):
        if isinstance(condition, (int, long)):
            do_(cls.table.delete(cls.c.id==condition, **kwargs))
        elif isinstance(condition, (tuple, list)):
            do_(cls.table.delete(cls.c.id.in_(condition)))
        else:
            do_(cls.table.delete(condition, **kwargs))
            
    @classmethod
    def count(cls, condition=None, **kwargs):
        count = do_(cls.table.count(condition, **kwargs)).scalar()
        return count
            
