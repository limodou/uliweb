#coding=utf8

from uliweb.orm import *

class Category(Model):
    name = Field(str, max_length=40)

class Blog(Model):
    title = Field(str, max_length=255)
    content = Field(TEXT)
