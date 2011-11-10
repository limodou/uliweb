#coding=utf8
import uliweb

def startup(sender):
    from uliweb import orm, settings
    from uliweb.core.SimpleFrame import __app_alias__
    from sae.core import Application
    
    orm.set_debug_query(settings.ORM.DEBUG_LOG)
    orm.set_auto_create(settings.ORM.AUTO_CREATE)
    
    #if AUTO_SAE_ORM_PARA==True, then use sae to get mysql parameters
    if settings.ORM.AUTO_SAE_ORM_PARA:
        app = Application()
        
        CONNECTION = settings.ORM.CONNECTION.format(username=app.mysql_user,
        password=app.mysql_pass, host=app.mysql_host, port=app.mysql_port,
        database=app.mysql_db)
        settings.ORM.CONNECTION = CONNECTION
        
#    orm.get_connection(settings.ORM.CONNECTION, **settings.ORM.CONNECTION_ARGS)

    if 'MODELS' in uliweb.settings:
        for name, path in uliweb.settings.MODELS.items():
            for k, v in __app_alias__.iteritems():
                if path.startswith(k):
                    path = v + path[len(k):]
                    break
            orm.set_model(path, name)
