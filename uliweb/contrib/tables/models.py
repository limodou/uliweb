#coding=utf-8

from uliweb.orm import Model, Field, get_model as _get_model
from uliweb.utils.common import get_var
import datetime

class Tables(Model):
    table_name =Field(str, max_length=40, verbose_name="表名", required=True)
    verbose_name = Field(str, max_length=255, verbose_name="说明")
    
    @classmethod
    def get_table(cls, tablename):
        obj = cls.get(cls.c.table_name == tablename)
        if not obj: 
            obj = Tables(table_name=tablename, verbose_name=tablename)
            obj.save()
        return obj
    
    @classmethod
    def get_model(cls, table):
        if isinstance(table, int):
            obj = cls.get(cls.c.id == table)
        else:
            obj = cls.get(cls.c.table_name == table)
        if obj:
            return _get_model(obj.table_name)
        
    @classmethod
    def get_object(cls, table, object_id):
        model = cls.get_model(table)
        if not model:
            raise Error('Table %r is not existed' % table)
        return model.get(object_id)
    
    def __unicode__(self):
        if self.table_name == self.verbose_name:
            return self.table_name
        else:
            return u"%s(%s)" % (self.table_name, self.verbose_name)
