import uliweb

def startup(sender):
    from uliweb import orm, settings
    from uliweb.core.SimpleFrame import __app_alias__
    from sae.core import Application
    
    app = Application()
    
    orm.set_debug_query(uliweb.settings.ORM.DEBUG_LOG)
    orm.set_auto_create(uliweb.settings.ORM.AUTO_CREATE)
    
    CONNECTION = uliweb.settings.ORM.CONNECTION.format(username=app.mysql_user,
        password=app.mysql_pass, host=app.mysql_host, port=app.mysql_port,
        database=app.mysql_db)
    uliweb.settings.ORM.CONNECTION = CONNECTION
    orm.get_connection(CONNECTION, **settings.ORM.CONNECTION_ARGS)

    if 'MODELS' in uliweb.settings:
        for name, path in uliweb.settings.MODELS.items():
            for k, v in __app_alias__.iteritems():
                if path.startswith(k):
                    path = v + path[len(k):]
                    break
            orm.set_model(path, name)
