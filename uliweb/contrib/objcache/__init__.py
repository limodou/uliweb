from uliweb import functions
from uliweb.utils.common import log, flat_list

def get_fields(tablename):
    from uliweb import settings
    
    tables = settings.get_var('OBJCACHE_TABLES')
    if not tablename in tables:
        return 
    
    return tables[tablename]

def get_id(tablename, id):
    return "objcache:%s:%d" % (tablename, id)

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
    
def get_object(model, tablename, id):
    """
    Get cached object from redis
    
    if id is None then return None:
    """
    from uliweb.utils.common import log
    
    if not id:
        return 
    
    if not check_enable():
        return
    
    redis = get_redis()
    if not redis: return
    _id = get_id(tablename, id)
    try:
        if redis.exists(_id):
            v = redis.hgetall(_id)
            o = model.load(v)
            log.debug("objcache:get:id="+_id)
            return o
    except Exception, e:
        log.exception(e)
        
def set_object(model, tablename, instance, fields=None):
    """
    Only support simple condition, for example: Model.c.id == n
    """
    from uliweb import settings
    from uliweb.utils.common import log
    
    if not check_enable():
        return
    
    if not fields:
        fields = get_fields(tablename)
    if fields:
        redis = get_redis()
        if not redis: return
        
        v = instance.dump(fields)
        _id = get_id(tablename, instance.id)
        try:
            pipe = redis.pipeline()
            r = pipe.delete(_id).hmset(_id, v).expire(_id, settings.get_var('OBJCACHE/timeout')).execute()
            log.debug("objcache:set:id="+_id)
        except Exception, e:
            log.exception(e)
        
    else:
        log.debug("There is no fields defined or not configured, so it'll not saved in cache, [%s:%d]" % (tablename, instance.id))
        
def post_save(model, instance, created, data, old_data):
    from uliweb.utils.common import log
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
    from uliweb.utils.common import log
    from uliweb import response

    if not check_enable():
        return
    
    tablename = model.tablename
    
    if get_fields(tablename):
        def f():
            _id = get_id(tablename)
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
        