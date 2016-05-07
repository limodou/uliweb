import re
import time
__connection_pool__ = None

def get_redis(**options):
    """
    if no options defined, then it'll use settings options
    
    #unix_socket_path = '/tmp/redis.sock'
    connection_pool = {'host':'localhost', 'port':6379}
    #if test after created redis client object
    test_first = False
    
    """
    from uliweb import settings
    from uliweb.utils.common import log
    import redis
        
    options = (options or {})
    options.update(settings.REDIS)
    if 'unix_socket_path' in options:
        client = redis.Redis(unix_socket_path=options['unix_socket_path'])
    else:
        global __connection_pool__
    
        if not __connection_pool__ or __connection_pool__[0] != options['connection_pool']:
            d = {'host':'localhost', 'port':6379}
            d.update(options['connection_pool'])
            __connection_pool__ = (d, redis.ConnectionPool(**d))
        client = redis.Redis(connection_pool=__connection_pool__[1])
        
    if settings.REDIS.test_first:
        try:
            client.info()
        except Exception as e:
            log.exception(e)
            client = None
    return client

def get_lock(key, value=None, expiry_time=60):
    """Get a distribute lock"""
    from uliweb.utils.common import get_uuid

    redis = get_redis()
    value = value or get_uuid()
    return redis.set(key, value, ex=expiry_time, nx=True)

def set_lock(key, value=None, expiry_time=60):
    """Force to set a distribute lock"""
    from uliweb.utils.common import get_uuid

    redis = get_redis()
    value = value or get_uuid()
    return redis.set(key, value, ex=expiry_time, xx=True)

re_compare_op = re.compile(r'^[><=]+')
def after_init_apps(sender):
    """
    Check redis version
    """
    from uliweb import settings
    from uliweb.utils.common import log
    
    check = settings.get_var('REDIS/check_version')
    if check:
        client = get_redis()
        try:
            info = client.info()
        except Exception as e:
            log.exception(e)
            log.error('Redis is not started!')
            return
        
        redis_version = info['redis_version']
        version = tuple(map(int, redis_version.split('.')))
        op = re_compare_op.search(check)
        if op:
            _op = op.group()
            _v = check[op.end()+1:].strip()
        else:
            _op = '='
            _v = check
        nv = tuple(map(int, _v.split('.')))
        if _op == '=':
            flag = version[:len(nv)] == nv
        elif _op == '>=':
            flag = version >= nv
        elif _op == '>':
            flag = version > nv
        elif _op == '<=':
            flag = version <= nv
        elif _op == '<':
            flag = version < nv
        else:
            log.error("Can't support operator %s when check redis version" % _op)
        if not flag:
            log.error("Redis version %s is not matched what you want %s" % (redis_version, _v))
            
        
def clear_prefix(prefix):
    redis = get_redis()
    if redis:
        text = """
local n = 0
for _,k in ipairs(redis.call('keys', ARGV[1])) do 
    redis.call('del', k)
    n = n + 1
end
return n
"""
        script = redis.register_script(text)
        pipe = redis.pipeline()
        script(args=[prefix], client=pipe)
        r = pipe.execute()
        return r[0]
        
    return 0

def count_prefix(prefix):
    redis = get_redis()
    if redis:
        text = """
local n = 0
for _,k in ipairs(redis.call('keys', ARGV[1])) do
    n = n + 1
end
return n
"""
        script = redis.register_script(text)
        pipe = redis.pipeline()
        script(args=[prefix], client=pipe)
        r = pipe.execute()
        return r[0]

    return 0

def mbrpoplpush(lists, deslist, timeout=0):

    redis = get_redis()
    if redis:
        text = """
local ret
for i, k in pairs(KEYS) do
    ret = redis.call('rpoplpush', k, ARGV[1])
    if ret then
        return {k, ret}
    end
end
"""
        script = redis.register_script(text)

        end = time.time() + timeout
        while 1:
            r = script(keys=lists, args=[deslist], client=redis)
            if r:
                return r
            if time.time() < end:
                time.sleep(.001)
            else:
                break
