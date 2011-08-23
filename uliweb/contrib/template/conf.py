from uliweb.form import *

class ManageForm(Form):
    use_template_temp_dir = BooleanField(label='Use template temp dir:', key='TEMPLATE/USE_TEMPLATE_TEMP_DIR')
    template_temp_dir = StringField(label='Template temp dir:', required=True, key='TEMPLATE/TEMPLATE_TEMP_DIR')