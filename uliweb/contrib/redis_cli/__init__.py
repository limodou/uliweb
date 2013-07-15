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
        
    options = (options or {}).update(settings.REDIS)
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
    