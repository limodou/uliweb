from uliweb.form import *

class ManageForm(Form):
    static_url = StringField(label='Static URL prefix:', required=True, key='wsgi_middleware_staticfiles/STATIC_URL')