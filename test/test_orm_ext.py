#coding=utf-8
#Test orm extension support

import time, sys
sys.path.insert(0, '../uliweb/lib')
from uliweb.core import dispatch
from uliweb.orm import *
import uliweb.orm
uliweb.orm.__auto_create__ = True
uliweb.orm.__nullable__ = True
uliweb.orm.__server_default__ = False

@dispatch.bind('get_model')
def _get_model(sender, model_name, model_inst, model_info, model_config):
    print 'hook:get_model model_name=%s' % model_name
    if model_config.get('__ext_model__'):
        print model_config['__ext_model__']
        M = get_model(model_config['__ext_model__'], refresh=True)
        if M:
            field_name = model_config.get('__ext_model_reference_field__', '_parent')
            M.OneToOne(field_name, model_inst, collection_name='ext')
    return model_inst

#basic testing
def test_get_model():
    """
    >>> db = get_connection('sqlite://')
    >>> db.metadata.drop_all()
    >>> class User(Model):
    ...     username = Field(unicode)
    ...     year = Field(int, default=30)
    ...     birth = Field(datetime.date)
    >>> class User_Extension(Model):
    ...     _parent = Field(PKTYPE())
    ...     name = Field(str)
    >>> set_model_config('user', {'__ext_model__':'user_extension', '__ext_model_reference_field__':'_parent'})
    >>> from uliweb.orm import __models__
    >>> U = get_model('user')
    hook:get_model model_name=user
    user_extension
    hook:get_model model_name=user_extension
    >>> U
    <class 'test_orm_ext.User'>
    >>> engine_manager['default'].models.keys()
    ['user', 'user_extension']
    >>> a1 = U(username='limodou')
    >>> a1.save()
    True
    >>> a1.ext
    <User_Extension {'_parent':<OneToOne:1>,'name':u'','id':1}>
    >>> a1.ext.name = 'hello'
    >>> a1.ext.save()
    True
    >>> b = U.get(1)
    >>> b.ext
    <User_Extension {'_parent':<OneToOne:1>,'name':u'hello','id':1}>
    >>> User_Extension.count()
    1
    >>> b.delete() #test delete reversed onetoone record also
    >>> User_Extension.count()
    0
    >>> c = U(username='limodou')
    >>> c.save()
    True
    >>> c.delete()
    """