from uliweb import functions
from logging import getLogger

log = getLogger(__name__)

def get_fields(tablename):
    from uliweb import settings
    
    tables = settings.get_var('OBJCACHE_TABLES')
    if not tablename in tables:
        return 
    
    fields = tables[tablename]
    if not isinstance(fields, (tuple, list)):
        fields = fields.get('fields', [])
    return fields

def get_id(engine, tablename, id):
    from uliweb import settings

    d = {'engine':engine, 'tablename':str(tablename), 'id':str(id)}
    format = settings.get_var('OBJCACHE/key_format', 'OC:%(engine)s:%(tablename)s:%(id)s')
    return format % d

def get_redis():
    try:
        redis = functions.get_redis()
    except Exception, e:
        log.exception(e)
        redis = None
    return redis

def check_enable():
    from uliweb import settings
    
    if settings.OBJCACHE.enable:
        return True
    
def get_object(model, tablename, id, engine_name):
    """
    Get cached object from redis
    
    if id is None then return None:
    """
    
    if not id:
        return 
    
    if not check_enable():
        return
    
    redis = get_redis()
    if not redis: return
    _id = get_id(engine_name or model.get_engine_name(), tablename, id)
    try:
        if redis.exists(_id):
            v = redis.hgetall(_id)
            o = model.load(v)
            log.debug("objcache:get:id="+_id)
            return o
    except Exception, e:
        log.exception(e)
        
def set_object(model, tablename, instance, fields=None, engine_name=None):
    """
    Only support simple condition, for example: Model.c.id == n
    if not id provided, then use instance.id
    """
    from uliweb import settings
    
    if not check_enable():
        return
    
    if not fields:
        fields = get_fields(tablename)

    redis = get_redis()
    if not redis: return
    
    v = instance.dump(fields)
    info = settings.get_var('OBJCACHE_TABLES/%s' % tablename)
    expire = settings.get_var('OBJCACHE/timeout', 0)
    key = 'id'
    if info and isinstance(info, dict):
        expire = info.get('expire', expire)
        key = info.get('key', key)
    
    if callable(key):
        _key = key(instance)
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
        log.debug("objcache:set:id="+_id+expire_msg)
    except Exception, e:
        log.exception(e)
        
def post_save(model, instance, created, data, old_data):
    from uliweb import response

    if not check_enable():
        return
    
    tablename = model.tablename
    
    fields = get_fields(tablename)
    if fields:
        #if response is False, then it means you may in batch program
        #so it can't use post_commit machenism
        def f():
            #check if the record has changed
            flag = created
            if not flag:
                flag = bool(filter(lambda x:x in data, fields))
            if flag:
                set_object(model, tablename, instance)
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
    
    if get_fields(tablename):
        def f():
            info = settings.get_var('OBJCACHE_TABLES/%s' % tablename)
            key = 'id'
            if info and isinstance(info, dict):
                key = info.get('key', key)
            if callable(key):
                _key = key(instance)
            else:
                _key = getattr(instance, key)
            
            _id = get_id(model.get_engine_name(), tablename, _key)
            redis = get_redis()
            if not redis: return
            
            try:
                redis.delete(_id)
                log.debug("objcache:post_delete:id="+_id)
            except Exception, e:
                log.exception(e)
            
        if response:
            response.post_commit = f
        else:
            f()
        