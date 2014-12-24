from uliweb.orm import *
from uliweb.utils.common import get_var
from uliweb.i18n import ugettext_lazy as _

class Model_Config(Model):
    model_name = Field(str, verbose_name=_('Model Name'), unique=True)
    display_name = Field(str, verbose_name=_('Display Name'))
    description = Field(str, verbose_name=_('Description'), max_length=255)
    uuid = Field(CHAR, verbose_name=_('UUID'), max_length=32)
    modified_user = Reference('user', verbose_name=_('Modified User'))
    modified_time = Field(datetime.datetime, verbose_name=_('Modified Time'),
                          auto_now=True, auto_now_add=True)
    published_time = Field(datetime.datetime, verbose_name=_('Published Time'))
    version = Field(int)

    def __unicode__(self):
        return "%s(%s)" % (self.model_name, self.uuid)

    def get_instance(self):
        MCH = get_model('model_config_his', signal=False)
        return MCH.get((MCH.c.model_name==self.model_name) & (MCH.c.uuid==self.uuid))

    @classmethod
    def OnInit(cls):
        Index('model_cfg_idx', cls.c.model_name, cls.c.uuid)

class Model_Config_His(Model):
    model_name = Field(str, verbose_name=_('Model Name'), index=True, required=True)
    display_name = Field(str, verbose_name=_('Display Name'))
    description = Field(str, verbose_name=_('Description'), max_length=255)
    table_name = Field(str, verbose_name=_('Tablename'))
    uuid = Field(CHAR, max_length=32)
    basemodel = Field(str, verbose_name=_('Base Model Class'),
                      hint=_('Underlying model class path'))
    has_extension = Field(bool, verbose_name=_('Has Extension Model'))
    extension_model = Field(str, verbose_name=_('Extension Model Class'),
                      hint=_('Underlying model class path'))
    fields = Field(TEXT)
    indexes = Field(TEXT)
    extension_fields = Field(TEXT)
    extension_indexes = Field(TEXT)
    version = Field(int)
    status = Field(CHAR, max_length=1, verbose_name=_('Publish Status'),
                   choices=get_var('MODEL_SETTING/'), default='0')
    create_time = Field(datetime.datetime, verbose_name=_('Create Time'), auto_now_add=True)
    published_time = Field(datetime.datetime, verbose_name=_('Published Time'))

    @classmethod
    def OnInit(cls):
        Index('model_cfg_his_idx', cls.c.model_name, cls.c.uuid)

