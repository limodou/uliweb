from uliweb.core.dispatch import bind
import uliweb

@bind('after_init_apps')
def startup(sender):
    from uliweb import orm
    
    orm.set_debug_query(uliweb.settings.ORM.DEBUG_LOG)
    orm.set_auto_create(uliweb.settings.ORM.AUTO_CREATE)
    orm.get_connection(uliweb.settings.ORM.CONNECTION, **uliweb.settings.ORM.CONNECTION_ARGS)

    if 'MODELS' in uliweb.settings:
        for k, v in uliweb.settings.MODELS.items():
            orm.set_model(v, k)