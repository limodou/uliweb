__connection_pool__ = None

def get_redis():
    from uliweb import settings
    import redis
        
    options = settings.REDIS
    if 'unix_socket_path' in options:
        client = redis.Redis(unix_socket_path=options['unix_socket_path'])
    else:
        global __connection_pool__
    
        if not __connection_pool__ or __connection_pool__[0] != options['connection_pool']:
            d = {'host':'localhost', 'port':6379}
            d.update(options['connection_pool'])
            __connection_pool__ = (d, redis.ConnectionPool(**d))
        client = redis.Redis(connection_pool=__connection_pool__[1])
    return client
    