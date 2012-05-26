#coding=utf8
import uliweb

def after_init_settings(sender):
    from uliweb import orm, settings
    
    #if AUTO_SAE_ORM_PARA==True, then use sae to get mysql parameters
    if settings.ORM.AUTO_SAE_ORM_PARA:
        import sae.const as const
        CONNECTION = settings.ORM.CONNECTION.format(username=const.MYSQL_USER,
        password=const.MYSQL_PASS, host=const.MYSQL_HOST, port=const.MYSQL_PORT,
        database=const.MYSQL_DB)
        
        settings.ORM.CONNECTION = CONNECTION
