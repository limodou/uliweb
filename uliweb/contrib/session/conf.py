from uliweb.form import *

class ManageForm(Form):
    type = SelectField(label='Session Type:', default='file', choices=[('file', 'File Based'), ('dbm', 'DMB Based'), ('database', 'Database Based')], key='SESSION/type')
    url = StringField(label='Connection URL(For Database):', default='sqlite:///session.db', key='SESSION_STORAGE/url')
    table_name = StringField(label='Table name(For Database):', default='uliweb_session', key='SESSION_STORAGE/table_name')
    data_dir = StringField(label='Session Path(File,DBM):', default='./sessions', key='SESSION_STORAGE/data_dir')
    timeout = IntField(label='Timeout:', required=True, default=3600, key='SESSION/timeout')
    cookie_timeout = IntField(label='Cookie Expire Time:', default=None, key='SESSION_COOKIE/timeout')
    cookie_domain = StringField(label='Cookie Domain:', default=None, key='SESSION_COOKIE/domain')
    cookie_path = StringField(label='Cookie Path:', default='/', key='SESSION_COOKIE/path')
    cookie_path = BooleanField(label='Cookie Secure:', default=False, key='SESSION_COOKIE/secure')
