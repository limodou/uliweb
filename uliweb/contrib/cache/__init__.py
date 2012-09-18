def get_cache(**kwargs):
    from uliweb import settings
    from weto.cache import Cache
    from uliweb.utils.common import import_attr, application_path

    serial_cls_path = settings.get_var('CACHE/serial_cls')
    if serial_cls_path:
        serial_cls = import_attr(serial_cls_path)
    else:
        serial_cls = None
        
    options = dict(settings.get_var('CACHE_STORAGE', {}))
    options['data_dir'] = application_path(options['data_dir'])
    args = {'storage_type':settings.get_var('CACHE/type'),
        'options':options,
        'expiry_time':settings.get_var('CACHE/expiretime'),
        'serial_cls':serial_cls}
        
    args.update(kwargs)
    cache = Cache(**args)
    return cache

