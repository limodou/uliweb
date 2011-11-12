import uliweb

def after_init_apps(sender):
    from uliweb import orm
    from uliweb.core.SimpleFrame import __app_alias__
    
    orm.set_debug_query(uliweb.settings.ORM.DEBUG_LOG)
    orm.set_auto_create(uliweb.settings.ORM.AUTO_CREATE)
    orm.get_connection(uliweb.settings.ORM.CONNECTION, **uliweb.settings.ORM.CONNECTION_ARGS)

    if 'MODELS' in uliweb.settings:
        for name, path in uliweb.settings.MODELS.items():
            for k, v in __app_alias__.iteritems():
                if path.startswith(k):
                    path = v + path[len(k):]
                    break
            orm.set_model(path, name)