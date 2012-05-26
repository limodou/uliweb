#coding=utf8
import uliweb

def after_init_settings(sender):
    from uliweb import orm, settings
    
    import sae.const as const
    CONNECTION = settings.ORM.CONNECTION.format(username=const.MYSQL_USER,
    password=const.MYSQL_PASS, host=const.MYSQL_HOST, port=const.MYSQL_PORT,
    database=const.MYSQL_DB)
    
    settings.ORM.CONNECTION = CONNECTION
