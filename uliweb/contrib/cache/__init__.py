def get_cache(**kwargs):
    from uliweb import settings
    from weto.cache import Cache
    from uliweb.utils.common import import_attr

    serial_cls_name = settings.get_var('CACHE/serial_cls', 'weto.cache.Serial')
    args = {'storage_type':settings.get_var('CACHE/type'),
        'options':settings.get_var('CACHE_STORAGE'),
        'expiry_time':settings.get_var('CACHE/expiretime'),
        'serial_cls':import_attr(serial_cls_name)}
        
    args.update(kwargs)
    cache = Cache(**args)
    return cache

