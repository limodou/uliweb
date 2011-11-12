#coding=utf8
import uliweb

def after_init_apps(sender):
    from uliweb import orm, settings
    from uliweb.core.SimpleFrame import __app_alias__
    
    orm.set_debug_query(settings.ORM.DEBUG_LOG)
    orm.set_auto_create(settings.ORM.AUTO_CREATE)
    
    #if AUTO_SAE_ORM_PARA==True, then use sae to get mysql parameters
    if settings.ORM.AUTO_SAE_ORM_PARA:
        import sae.const
        CONNECTION = settings.ORM.CONNECTION.format(username=sae.const.MYSQL_USER,
        password=sae.const.MYSQL_PASS, host=sae.const.MYSQL_HOST, port=sae.const.MYSQL_PORT,
        database=sae.const.MYSQL_DB)
        settings.ORM.CONNECTION = CONNECTION
        
    if 'MODELS' in uliweb.settings:
        for name, path in uliweb.settings.MODELS.items():
            for k, v in __app_alias__.iteritems():
                if path.startswith(k):
                    path = v + path[len(k):]
                    break
            orm.set_model(path, name)
