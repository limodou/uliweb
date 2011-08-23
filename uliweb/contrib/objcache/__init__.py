import datetime
from decimal import Decimal
from uliweb import function

def get_key(tablename):
    from uliweb import settings
    
    tables = settings.get_var('OBJCACHE/config')
    if not tablename in tables:
        return 
    
    return tables[tablename]

def get_id(tablename, condition):
    from uliweb.utils.common import safe_str
    return "__objcache__:%s:%s" % (tablename, safe_str(condition.right.value))

def get_cache():
    from weto.cache import NoSerial
    return function('get_cache')(serial_cls=NoSerial)
    
def get_object(sender, condition):
    """
    Only support simple condition, for example: Model.c.id == n
    """
    from sqlalchemy.sql.expression import _BinaryExpression
    from uliweb.utils.common import log
    
    tablename = sender.tablename
    log.debug("get:begin")
    
    _key = get_key(tablename)
    log.debug("get:_key="+_key)
    if _key and (isinstance(condition, _BinaryExpression) and
        (condition.left.name == _key)):
        cache = get_cache()
        _id = get_id(tablename, condition)
        log.debug("get:id=" + _id)
        v = cache.get(_id, None)
        log.debug("get:value="+str(v))
        if v:
            d = eval(v)
            o = sender(**d)
            o.set_saved()
            return o
        
def set_object(sender, condition, instance):
    """
    Only support simple condition, for example: Model.c.id == n
    """
    from sqlalchemy.sql.expression import _BinaryExpression
    from uliweb import settings
    from uliweb.utils.common import log
    
    tablename = sender.tablename
    
    _key = get_key(tablename)
    if _key and (isinstance(condition, _BinaryExpression) and (condition.left.name == _key)):
        v = repr(instance.to_dict())
        cache = get_cache()
        _id = get_id(tablename, condition)
        log.debug("set:id=" + _id)
        ret = cache.set(_id, v, settings.get_var('OBJCACHE/expiry_time'))
        log.debug("set:value="+v)
        return ret
        
def post_save(sender, instance, created, data, old_data):
    from uliweb.utils.common import log
    from uliweb import settings

    tablename = sender.tablename
    
    _key = get_key(tablename)
    if _key:
        _id = get_id(tablename, sender.c[_key]==instance.id)
        log.debug("post_save:id=" + _id)
        cache = get_cache()
        v = repr(instance.to_dict())
        log.debug("post_save:value="+v)
        ret = cache.set(_id, v, settings.get_var('OBJCACHE/expiry_time'))
        return ret

def post_delete(sender, instance):
    from uliweb.utils.common import log

    tablename = sender.tablename
    
    _key = get_key(tablename)
    if _key:
        _id = get_id(tablename, sender.c[_key]==instance.id)
        log.debug("post_delete:id=" + _id)
        cache = get_cache()
        ret = cache.delete(_id)
        return ret
    