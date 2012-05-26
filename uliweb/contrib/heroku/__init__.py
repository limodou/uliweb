#coding=utf8
import os
import uliweb

def after_init_settings(sender):
    from uliweb import settings
    settings.ORM.CONNECTION = os.environ['DATABASE_URL']
