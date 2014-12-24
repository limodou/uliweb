#coding=utf-8
#Test orm extension support

import time, sys
sys.path.insert(0, '../uliweb/lib')
from uliweb.core import dispatch
from uliweb.orm import *
import uliweb.orm as orm
orm.__auto_create__ = True
orm.__nullable__ = True
orm.__server_default__ = False

def _get_model(sender, model_name, model_inst, model_info, model_config):
    print 'hook:get_model model_name=%s' % model_name
    if model_config.get('__ext_model__'):
        print model_config['__ext_model__']
        M = get_model(model_config['__ext_model__'], signal=False)
        if M:
            field_name = model_config.get('__ext_model_reference_field__', '_parent')
            M.OneToOne(field_name, model_inst, collection_name='ext')
    return model_inst

#basic testing
def test_get_model():
    """
    >>> db = get_connection('sqlite://')
    >>> db.metadata.drop_all()
    >>> set_auto_create(True)
    >>> orm.__models__ = {}
    >>> class User(Model):
    ...     username = Field(unicode)
    ...     year = Field(int, default=30)
    ...     birth = Field(datetime.date)
    >>> class User_Extension(Model):
    ...     _parent = Field(PKTYPE())
    ...     name = Field(str)
    >>> set_model_config('user', {'__ext_model__':'user_extension', '__ext_model_reference_field__':'_parent'})
    >>> f = dispatch.bind('post_get_model')(_get_model)
    >>> U = get_model('user')
    hook:get_model model_name=user
    user_extension
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
    >>> dispatch.unbind('post_get_model', _get_model)
    """

def _get_model_1(sender, model_name, model_inst, model_info, model_config):
    if model_name == 'user':
        fields = [
            {'name':'username', 'type':'str'},
            {'name':'year', 'type':'int', 'default':30},
            {'name':'birth', 'type':'datetime.date'},
        ]
        return create_model(model_name, fields)

def _get_model_2(sender, model_name, model_inst, model_info, model_config):
    if model_name == 'user':
        fields = [
            {'name':'username', 'type':'str'},
            {'name':'year', 'type':'int', 'default':30},
            {'name':'birth', 'type':'datetime.date'},
            {'name':'active', 'type':'bool'},
        ]
        return create_model(model_name, fields)

def _get_model_3(sender, model_name, model_inst, model_info, model_config):
    print 'hook:get_model model_name=%s' % model_name
    ext_name = model_config.get('__ext_model__')
    if ext_name:
        print ext_name

        fields = [
            {'name':'_parent', 'type':'OneToOne', 'reference_class':'user', 'collection_name':'ext'},
            # {'name':'_parent', 'type':'int'},
            {'name':'name', 'type':'str'},
        ]
        x = create_model(ext_name, fields)
        #x.OneToOne('_parent', model_inst, collection_name='ext')
    return model_inst

def _get_model_4(sender, model_name, model_inst, model_info, model_config):
    print 'hook:get_model model_name=%s' % model_name
    ext_name = model_config.get('__ext_model__')
    if ext_name:
        print ext_name

        fields = [
            {'name':'_parent', 'type':'OneToOne', 'reference_class':'user', 'collection_name':'ext'},
            # {'name':'_parent', 'type':'int'},
            {'name':'name', 'type':'str'},
            {'name':'active', 'type':'bool'},
        ]
        x = create_model(ext_name, fields)
        #x.OneToOne('_parent', model_inst, collection_name='ext')
    return model_inst

def _find_model(sender, model_name):
    import uliweb.orm as orm

    if model_name == 'user':
        set_model(model_name, model_name, appname=__name__, model_path='')
        return orm.__models__.get(model_name)

#basic testing
def test_dynamic_model():
    """
    >>> db = get_connection('sqlite://')
    >>> db.metadata.drop_all()
    >>> set_auto_create(False)
    >>> orm.__models__ = {}
    >>> f = dispatch.bind('get_model')(_get_model_1)
    >>> f1 = dispatch.bind('find_model')(_find_model)
    >>> U = get_model('user')
    >>> U.create()
    >>> U.properties.keys()
    ['username', 'id', 'birth', 'year']
    >>> a1 = U(username='limodou')
    >>> a1.save()
    True
    >>> b = U.get(1)
    >>> b
    <User {'username':u'limodou','year':30,'birth':None,'id':1}>
    >>> dispatch.unbind('get_model', _get_model_1)
    >>> f = dispatch.bind('get_model')(_get_model_2)
    >>> U = get_model('user')
    >>> U.properties.keys()
    ['username', 'active', 'id', 'birth', 'year']
    >>> dispatch.unbind('find_model', _find_model)
    >>> dispatch.unbind('get_model', _get_model_2)
    """

def test_get_extension_model():
    """
    >>> db = get_connection('sqlite://')
    >>> db.metadata.drop_all()
    >>> set_auto_create(False)
    >>> orm.__models__ = {}
    >>> from sqlalchemy import *
    >>> class User(Model):
    ...     username = Field(unicode)
    ...     year = Field(int, default=30)
    ...     birth = Field(datetime.date)
    >>> User.create()
    >>> UE = Table('user_extension', db.metadata,
    ...     Column('id', INT, primary_key=True, autoincrement=True),
    ...     Column('_parent', INT),
    ...     Column('name', VARCHAR(255)))
    >>> UE.create()
    >>> set_model_config('user', {'__ext_model__':'user_extension', '__ext_model_reference_field__':'_parent'})
    >>> f = dispatch.bind('post_get_model')(_get_model_3)
    >>> U = get_model('user')
    hook:get_model model_name=user
    user_extension
    >>> U
    <class 'test_orm_ext.User'>
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
    >>> UE = get_model('user_extension')
    hook:get_model model_name=user_extension
    >>> UE.count()
    1
    >>> b.delete() #test delete reversed onetoone record also
    >>> UE.count()
    0
    >>> c = U(username='limodou')
    >>> c.save()
    True
    >>> c.delete()
    >>> dispatch.unbind('post_get_model', _get_model_3)
    """

def test_migrate():
    """
    >>> db = get_connection('sqlite://')
    >>> db.metadata.drop_all()
    >>> set_auto_create(False)
    >>> orm.__models__ = {}
    >>> from sqlalchemy import *
    >>> class User(Model):
    ...     username = Field(unicode)
    ...     year = Field(int, default=30)
    ...     birth = Field(datetime.date)
    >>> User.create()
    >>> UE = Table('user_extension', db.metadata,
    ...     Column('id', INT, primary_key=True, autoincrement=True),
    ...     Column('_parent', INT),
    ...     Column('name', VARCHAR(255)))
    >>> UE.create()
    >>> set_model_config('user', {'__ext_model__':'user_extension', '__ext_model_reference_field__':'_parent'})
    >>> f = dispatch.bind('post_get_model')(_get_model_4)
    >>> U = get_model('user')
    hook:get_model model_name=user
    user_extension
    >>> T = get_model('user_extension')
    hook:get_model model_name=user_extension
    >>> migrate_tables(['user_extension'])
    >>> from sqlalchemy.engine.reflection import Inspector
    >>> inspector = Inspector.from_engine(db.connect())
    >>> print [x['name'] for x in inspector.get_columns('user_extension')]
    [u'id', u'_parent', u'name', u'active']
    """

def test_migrate_2():
    """
    >>> db = get_connection('sqlite://')
    >>> db.metadata.drop_all()
    >>> set_auto_create(False)
    >>> orm.__models__ = {}
    >>> from sqlalchemy import *
    >>> class User(Model):
    ...     username = Field(unicode)
    ...     year = Field(int, default=30)
    ...     birth = Field(datetime.date)
    >>> User.migrate()
    >>> from sqlalchemy.engine.reflection import Inspector
    >>> inspector = Inspector.from_engine(db.connect())
    >>> print [x['name'] for x in inspector.get_columns('user')]
    [u'username', u'year', u'birth', u'id']
    """

def test_migrate_3():
    """
    >>> db = get_connection('sqlite://')
    >>> db.metadata.drop_all()
    >>> set_auto_create(False)
    >>> orm.__models__ = {}
    >>> from sqlalchemy import *
    >>> class User(Model):
    ...     username = Field(unicode)
    ...     year = Field(int, default=30)
    ...     birth = Field(datetime.date)
    >>> class Group(Model):
    ...     users = ManyToMany('user')
    >>> User.migrate()
    >>> Group.migrate()
    >>> from sqlalchemy.engine.reflection import Inspector
    >>> inspector = Inspector.from_engine(db.connect())
    >>> inspector.get_table_names()
    [u'group', u'group_user_users', u'user']
    """

def test_extend_model():
    """
    >>> db = get_connection('sqlite://')
    >>> db.metadata.drop_all()
    >>> set_auto_create(False)
    >>> orm.__models__ = {}
    >>> from sqlalchemy import *
    >>> class User(Model):
    ...     username = Field(unicode)
    ...     year = Field(int, default=30)
    ...     birth = Field(datetime.date)
    >>> class User(User):
    ...     __replace__ = True
    ...     name = Field(str)
    >>> print User.properties.keys()
    ['name', 'id']
    >>> print User.table.columns.keys()
    ['name', 'id']
    """

