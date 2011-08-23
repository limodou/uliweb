from uliweb.form import *

class ManageForm(Form):
    to_path = StringField(label='Save Files to:', key='UPLOAD/TO_PATH')
    url_suffix = StringField(label='Uploaded files url suffix:', key='UPLOAD/URL_SUFFIX')
    buffer_size = IntField(label='Transfering buffer size:', key='UPLOAD/BUFFER_SIZE')
