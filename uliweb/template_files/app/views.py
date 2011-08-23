#coding=utf-8
from uliweb import expose

@expose('/')
def index():
    return '<h1>Hello, Uliweb</h1>'
