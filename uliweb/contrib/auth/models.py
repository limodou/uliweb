from uliweb.orm import *
import datetime
from uliweb.i18n import ugettext_lazy as _
from uliweb import functions
from . import encrypt_password, check_password
from uliweb.utils.common import get_var

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
    deleted = Field(bool, verbose_name=_('Deleted'))
    auth_type = Field(str, max_length=20, default='default', verbose_name=_('Auth type'))

    def set_password(self, raw_password):
        self.password = encrypt_password(raw_password)
        # self.save()

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
        return (self.nickname or self.username) + (_('(Deleted)') if self.deleted else '')

    class Meta:
        display_field = 'username'

    class AddForm:
        fields = ['username', 'nickname', 'email', 'is_superuser']

    class EditForm:
        fields = ['email']

    class AdminEditForm:
        fields = ['email', 'is_superuser']

    class DetailView:
        fields = ['username', 'nickname', 'email', 'is_superuser', 'date_join', 'last_login']

    class Table:
        fields = [
            {'name':'username'},
            {'name':'nickname'},
            {'name':'email'},
            {'name':'is_superuser'},
            {'name':'date_join'},
            {'name':'last_login'},
            {'name':'deleted'},
        ]

class UserGroup(Model):
    name = Field(str, max_length=128, verbose_name=_('Name'), index=True, nullable=True)
    parent = SelfReference(verbose_name=_('Parent Group'), collection_name='children', nullable=True, default=0)
    users = ManyToMany('user', verbose_name=_('Users'), collection_name='groups')
    deleted = Field(bool, verbose_name=_('Deleted'))
    created_time = Field(datetime.datetime, verbose_name=_('Created Datetime'), auto_now_add=True)
    number_of_children = Field(int, verbose_name=_('Number of Children'))
    number_of_people = Field(int, verbose_name=_('Number of People'))
    order = Field(int, verbose_name=_('Order'), default=9999)
    type = Field(CHAR, max_length=1, verbose_name=_('Group Type'), choices=get_var('AUTH/USER_GROUP_TYPE'))
    auth_type = Field(int, default=get_var('AUTH/AUTH_TYPE_DEFAULT'), verbose_name=_('Auth type'))

    def __unicode__(self):
        return self.name

    @classmethod
    def OnInit(cls):
        Index('usergroup_idx', cls.c.parent, cls.c.name)
