from uliweb.orm import *
from uliweb.utils.common import get_var

class Model_Config(Model):
    name = Field(str, unique=True, index=True)
    cur_uuid = Field(CHAR, max_length=32)
    modified_user = Reference('user')
    modified_time = Field(datetime.datetime, auto_now=True, auto_now_add=True)
    submitted_time = Field(datetime.datetime)
    version = Field(int)

    def __unicode__(self):
        return "%s(%s)" % (self.name, self.cur_uuid)

    def get_instance(self):
        MCH = get_model('model_config_his')
        return MCH.get((MCH.c.model_name==self.name) & (MCH.c.uuid==self.cur_uuid))

class Model_Config_His(Model):
    model_name = Field(str, index=True)
    table_name = Field(str)
    uuid = Field(CHAR, max_length=32)
    basemodel = Field(str)
    has_extension = Field(bool)
    extension_model = Field(str)
    fields = Field(TEXT)
    indexes = Field(TEXT)
    extension_fields = Field(TEXT)
    extension_indexes = Field(TEXT)
    version = Field(int)
    status = Field(CHAR, max_length=1, choices=get_var('MODEL_SETTING/'))

    @classmethod
    def OnInit(cls):
        Index('model_cfg_his_idx', cls.c.model_name, cls.c.uuid)

