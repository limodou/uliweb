from uliweb.orm import *
import datetime
from uliweb.i18n import ugettext_lazy as _
from uliweb import functions
from . import encrypt_password, check_password

class User(Model):
    username = Field(str, verbose_name=_('Username'), max_length=30, unique=True, index=True, nullable=False)
    nickname = Field(str, verbose_name=_('Nick Name'), max_length=30)
    email = Field(str, verbose_name=_('Email'), max_length=40)
    password = Field(str, verbose_name=_('Password'), max_length=128)
    is_superuser = Field(bool, verbose_name=_('Is Superuser'))
    last_login = Field(datetime.datetime, verbose_name=_('Last Login'), nullable=True)
    date_join = Field(datetime.datetime, verbose_name=_('Joined Date'), auto_now_add=True)
    image = Field(FILE, verbose_name=_('Portrait'), max_length=256)
    active = Field(bool, verbose_name=_('Active Status'))
    locked = Field(bool, verbose_name=_('Lock Status'))
    
    def set_password(self, raw_password):
        self.password = encrypt_password(raw_password)
        self.save()
    
    def check_password(self, raw_password):
        """
        Returns a boolean of whether the raw_password was correct. Handles
        encryption formats behind the scenes.
        """
        return check_password(raw_password, self.password)
    
    def get_image_url(self):
        if self.image:
            return functions.get_href(self.image)
        else:
            return functions.url_for_static('images/user%dx%d.jpg' % (50, 50))
        
    def get_default_image_url(self, size=50):
        return functions.url_for_static('images/user%dx%d.jpg' % (size, size))
        
    def __unicode__(self):
        return self.username
    
    class Meta:
        display_field = 'username'
        
    class AddForm:
        fields = ['username', 'email', 'is_superuser']
        
    class EditForm:
        fields = ['email']
        
    class AdminEditForm:
        fields = ['email', 'is_superuser']
        
    class DetailView:
        fields = ['username', 'email', 'is_superuser', 'date_join', 'last_login']
        
    class Table:
        fields = [
            {'name':'username'},
            {'name':'email'},
            {'name':'is_superuser'},
            {'name':'date_join'},
            {'name':'last_login'},
        ]
    
class UserGroup(Model):
    #use in grouptype
    GROUP_TYPE_NORMAL = 0
    GROUP_TYPE_LDAP = 1
    
    groupname = Field(str, verbose_name=_('Group name'), max_length=80, unique=True, index=True, nullable=False)
    grouptype = Field(int, verbose_name=_('Group type'), default=GROUP_TYPE_NORMAL)
    users = ManyToMany('user', collection_name='user_groups', nullable=True)
    
    def __unicode__(self):
        return self.groupname
