from uliweb import functions
from logging import getLogger
from uliweb.utils.common import import_attr

log = getLogger(__name__)

def get_fields(tablename):
    from uliweb import settings
    
    tables = settings.get_var('OBJCACHE_TABLES')
    if not tablename in tables:
        return [], []
    
    info = tables[tablename] or []
    if isinstance(info, (str, unicode)):
        info = [info]
    exclude = []
    if not isinstance(info, (tuple, list)):
        fields = info.get('fields', [])
        exclude = info.get('exclude', [])
    else:
        fields = info
    return fields, exclude

def get_id(engine, tablename, id=0, table_prefix=False):
    from uliweb import settings
    
    table = functions.get_table(tablename)
    d = {'engine':engine, 'tableid':table.id, 'id':str(id), 'tablename':tablename}
    if table_prefix:
        format = settings.get_var('OBJCACHE/table_format', 'OC:%(engine)s:%(tableid)d:')
    else:
        format = settings.get_var('OBJCACHE/key_format', 'OC:%(engine)s:%(tableid)d:%(id)s')
    return format % d

def clear_table(engine, tablename):
    prefix = get_id(engine, tablename, table_prefix=True) + '*'
    return functions.redis_clear_prefix(prefix)
        
def get_redis():
    try:
        redis = functions.get_redis()
    except Exception as e:
        log.exception(e)
        redis = None
    return redis

def check_enable():
    from uliweb import settings
    
    if settings.OBJCACHE.enable:
        return True
    
def get_object(model, cid, engine_name=None, connection=None):
    """
    Get cached object from redis
    
    if id is None then return None:
    """
    from uliweb import settings
    
    if not id:
        return 
    
    if not check_enable():
        return
    
    redis = get_redis()
    if not redis: return

    tablename = model._alias or model.tablename
    
    info = settings.get_var('OBJCACHE_TABLES/%s' % tablename, {})
    if info is None:
        return
    
    _id = get_id(engine_name or model.get_engine_name(), tablename, cid)
    try:
        log.debug("Try to find objcache:get:table=%s:id=[%s]" % (tablename, _id))
        if redis.exists(_id):
            v = redis.hgetall(_id)
            o = model.load(v, from_='dump')
            log.debug("Found!")
            return o
        else:
            log.debug("Not Found!")
    except Exception as e:
        log.exception(e)
       

def set_object(model, instance, fields=None, engine_name=None):
    """
    Only support simple condition, for example: Model.c.id == n
    if not id provided, then use instance.id
    """
    from uliweb import settings
    
    if not check_enable():
        return
    
    redis = get_redis()
    if not redis: return
    
    tablename = model._alias or model.tablename
    exclude = []
    if not fields:
        fields, exclude = get_fields(tablename)
    
    v = instance.dump(fields, exclude=exclude)
    info = settings.get_var('OBJCACHE_TABLES/%s' % tablename, {})
    
    if info is None:
        return
    
    expire = settings.get_var('OBJCACHE/timeout', 0)
    key = 'id'
    if info and isinstance(info, dict):
        expire = info.get('expire', expire)
        key = info.get('key', key)
    
    if '.' in key or key not in model.properties:
        _key = import_attr(key)(instance)
    else:
        _key = getattr(instance, key)
    _id = get_id(engine_name or model.get_engine_name(), tablename, _key)
    try:
        pipe = redis.pipeline()
        p = pipe.delete(_id).hmset(_id, v)
        expire_msg = ''
        if expire:
            p = p.expire(_id, expire)
            expire_msg = ':expire=%d' % expire
        r = p.execute()
        log.debug("Saving to cache objcache:set:table=%s:id=[%s]:%s" % (tablename, _id, expire_msg))
    except Exception as e:
        log.exception(e)
        
def post_save(model, instance, created, data, old_data):
    from uliweb import response, settings

    if not check_enable():
        return
    
    tablename = model.tablename
    if tablename not in settings.get_var('OBJCACHE_TABLES'):
        return
    
    #if response is False, then it means you may in batch program
    #so it can't use post_commit machenism
    def f():
        fields = get_fields(tablename)
        flag = created
        #if update then check if the record has changed
        if not flag:
            if not fields:
                flag = True
            else:
                fields = model.properties.keys()
                flag = bool(filter(lambda x:x in data, fields))
        if flag:
            set_object(model, instance)
            log.debug("objcache:post_save:id=%d" % instance.id)
    if response:
        response.post_commit = f
    else:
        f()
        
def post_delete(model, instance):
    from uliweb import response, settings

    if not check_enable():
        return
    
    tablename = model.tablename
    if tablename not in settings.get_var('OBJCACHE_TABLES'):
        return
    
    def f():
        redis = get_redis()
        if not redis: return

        info = settings.get_var('OBJCACHE_TABLES/%s' % tablename)
        key = 'id'
        if info and isinstance(info, dict):
            key = info.get('key', key)
        if '.' in key or key not in model.properties:
            _key = import_attr(key)(instance)
        else:
            _key = getattr(instance, key)
        
        _id = get_id(model.get_engine_name(), tablename, _key)
        
        try:
            redis.delete(_id)
            log.debug("objcache:post_delete:id="+_id)
        except Exception as e:
            log.exception(e)
    
    if response:
        response.post_commit = f
    else:
        f()
        