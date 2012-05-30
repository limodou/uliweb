#coding=utf-8

from uliweb.orm import *
from uliweb.utils.common import get_var
import datetime
from uliweb.i18n import gettext_lazy as _

class Tables(Model):
    tablename =Field(str, max_length=40, verbose_name=_('TableName'), required=True)
    verbose_name = Field(str, max_length=255, verbose_name=_('Description'))
    
    @classmethod
    def get_table(cls, tablename):
        obj = cls.get(cls.c.tablename == tablename)
        if not obj: 
            obj = Tables(tablename=tablename, verbose_name=tablename)
            obj.save()
        return obj
    
    def __unicode__(self):
        return self.verbose_name
