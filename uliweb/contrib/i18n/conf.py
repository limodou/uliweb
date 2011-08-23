from uliweb.form import *

class ManageForm(Form):
    language_code = StringField(label='Site Language Code:', key='I18N/LANGUAGE_CODE')
