from uliweb.orm import *
from uliweb.i18n import ugettext_lazy as _

class DBUploadFiles(Model):
    filename = Field(str, verbose_name=_('Filename'), max_length=255, index=True, required=True)
    content = Field(BLOB, verbose_name=_('File Content'))
    size = Field(int, verbose_name=_('Filesize'))
    create_time = Field(datetime.datetime, verbose_name=_('Create Time'), auto_now_add=True)
    download_times = Field(int, verbose_name=_('Download Times'))
    slug = Field(str, max_length=40, verbose_name=_('Slug'), index=True, unique=True)
    path = Field(str, max_length=255, verbose_name=_('File Path'))
    
    def __unicode__(self):
        return self.filename