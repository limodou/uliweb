#coding=utf8
import os
import uliweb

def after_init_settings(sender):
    from uliweb import orm, settings
    import bae.core.const as const
    
    #从环境变量里取出数据库连接需要的参数
    CONNECTION = settings.ORM.CONNECTION.format(username=const.MYSQL_USER,
    password=const.MYSQL_PASS, host=const.MYSQL_HOST, port=const.MYSQL_PORT,
    database=settings.ORM.DATABASE)
    settings.ORM.CONNECTION = CONNECTION
