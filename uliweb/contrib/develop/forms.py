from uliweb.form import *

class GenericForm(Form):
    debug = BooleanField(label='Debug:', key='GLOBAL/DEBUG')
    time_zone = StringField(label='Time Zone:', key='GLOBAL/TIME_ZONE', default='UTC')
    wsgi_middlewares = TextLinesField(label='WSGI Middlewares:', key='GLOBAL/WSGI_MIDDLEWARES')
    middlewares = TextLinesField(label='Middlewares:', key='GLOBAL/MIDDLEWARE_CLASSES')
