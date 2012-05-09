import uliweb

def after_init_apps(sender):
    from uliweb import orm, settings
    from uliweb.core.SimpleFrame import __app_alias__
    
    orm.set_debug_query(uliweb.settings.ORM.DEBUG_LOG)
    orm.set_auto_create(uliweb.settings.ORM.AUTO_CREATE)
    orm.set_auto_set_model(False)
    
    #judge if transaction middle has not install then set
    #AUTO_DOTRANSACTION is False
    if 'transaction' in settings.MIDDLEWARES:
        orm.set_auto_dotransaction(False)
    else:
        orm.set_auto_dotransaction(uliweb.settings.ORM.AUTO_DOTRANSACTION)
    
    d = {'connection_string':uliweb.settings.ORM.CONNECTION,
        'connection_type':uliweb.settings.ORM.CONNECTION_TYPE,
        'debug_log':uliweb.settings.ORM.DEBUG_LOG,
        'connection_args':uliweb.settings.ORM.CONNECTION_ARGS,
        'strategy':uliweb.settings.ORM.STRATEGY,
        }
    orm.engine_manager.add('default', d)
    
    for name, d in uliweb.settings.ORM.CONNECTIONS.items():
        x = {'connection_string':d.get('CONNECTION', ''),
            'debug_log':d.get('DEBUG_LOG', None),
            'connection_args':d.get('CONNECTION_ARGS', {}),
            'strategy':d.get('STRATEGY', 'threadlocal'),
            'connection_type':d.get('CONNECTION_TYPE', 'long')
        }
        orm.engine_manager.add(name, x)

    if 'MODELS' in uliweb.settings:
        for name, model_path in uliweb.settings.MODELS.items():
            if isinstance(model_path, (str, unicode)):
                path = model_path
                engine_name = 'default'
            else:
                path, engine_name = model_path
            for k, v in __app_alias__.iteritems():
                if path.startswith(k):
                    path = v + path[len(k):]
                    break
            orm.set_model(path, name, engine_name=engine_name)