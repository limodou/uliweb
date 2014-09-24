#coding=utf8

from uliweb.orm import *

class Sequence(Model):
    key = Field(str, max_length=80, required=True, unique=True, index=True)
    value = Field(int)
    version = Field(int)
    modified_time = Field(datetime.datetime, auto_now=True, auto_now_add=True)
    
    def __unicode__(self):
        return self.key+'/'+str(self.value)
