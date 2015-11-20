import os
from uliweb import manage
from uliweb.orm import *
import uliweb.orm as orm
from uliweb.manage import make_simple_application

os.chdir('test_orm_ext')
if os.path.exists('database.db'):
    os.remove('database.db')

manage.call('uliweb syncdb -v')

def test_extend_model():
    """
    >>> app = make_simple_application(project_dir='.', reuse=False)
    >>> U = get_model('user')
    >>> U.properties.keys()
    ['username', 'age', 'id']
    >>> U1 = get_model('user1')
    >>> U1.properties.keys()
    ['age', 'id']
    """

def test_dynamic_extend_model_1():
    """
    >>> app = make_simple_application(project_dir='.', reuse=False)
    >>> fields = [
    ...     {'name':'year', 'type':'int'}
    ... ]
    >>> U = create_model('user2', fields)
    >>> print U.properties.keys()
    ['id', 'year']
    """

def test_dynamic_extend_model_2():
    """
    >>> app = make_simple_application(project_dir='.', reuse=False)
    >>> fields = [
    ...     {'name':'year', 'type':'int'}
    ... ]
    >>> U = create_model('user3', fields, basemodel='uliweb.contrib.auth.models.User')
    >>> print U.properties.keys()
    ['username', 'locked', 'deleted', 'image', 'date_join', 'email', 'is_superuser', 'last_login', 'year', 'active', 'password', 'nickname', 'id']
    >>> print hasattr(U, 'check_password')
    True
    """

def test_dynamic_extend_model_3():
    """
    >>> app = make_simple_application(project_dir='.', reuse=False)
    >>> fields = [
    ...     {'name':'year', 'type':'int'}
    ... ]
    >>> U = create_model('user', fields, __replace__=True, basemodel='uliweb.contrib.auth.models.User')
    >>> U = get_model('user')
    >>> sql =  print_model(U, skipblank=True)
    >>> sql
    'CREATE TABLE user (year INTEGER, id INTEGER NOT NULL, PRIMARY KEY (id));'
    >>> print hasattr(U, 'check_password')
    True
    """

def test_dynamic_extend_model_4():
    """
    >>> app = make_simple_application(project_dir='.', reuse=False)
    >>> fields = [
    ...     {'name':'year', 'type':'int', '_reserved':True}
    ... ]
    >>> U = create_model('user3', fields, basemodel='uliweb.contrib.auth.models.User')
    >>> print U.properties.keys()
    ['username', 'locked', 'deleted', 'image', 'date_join', 'email', 'is_superuser', 'last_login', 'year', 'active', 'password', 'nickname', 'id']
    >>> print hasattr(U, 'check_password')
    True
    """

def test_create_model_index():
    """
    >>> app = make_simple_application(project_dir='.')
    >>> fields = [
    ...     {'name':'year', 'type':'int'}
    ... ]
    >>> indexes = [
    ...     {'name':'user_idx', 'fields':['year'], 'unique':True},
    ... ]
    >>> U = orm.create_model('user', fields, indexes=indexes,
    ...                      __replace__=True, basemodel='uliweb.contrib.auth.models.User')
    >>> U = get_model('user')
    >>> print print_model(U, skipblank=True)
    CREATE TABLE user (year INTEGER, id INTEGER NOT NULL, PRIMARY KEY (id));CREATE UNIQUE INDEX user_idx ON "user" (year);
    """

def test_recreate_model():
    """
    >>> app = make_simple_application(project_dir='.')
    >>> fields = [
    ...     {'name':'year', 'type':'int'},
    ...     {'name':'group', 'type':'Reference', 'reference_class':'usergroup', 'collection_name':'myusers'}
    ... ]
    >>> indexes = [
    ...     {'name':'user_idx', 'fields':['year'], 'unique':True},
    ... ]
    >>> U = orm.create_model('user', fields, indexes=indexes,
    ...                      __replace__=True, basemodel='uliweb.contrib.auth.models.User')
    >>> U = get_model('user')
    >>> print print_model(U, skipblank=True)
    CREATE TABLE user (year INTEGER, "group" INTEGER, id INTEGER NOT NULL, PRIMARY KEY (id));CREATE UNIQUE INDEX user_idx ON "user" (year);
    >>> U = orm.create_model('user', fields, indexes=indexes,
    ...                      __replace__=True, basemodel='uliweb.contrib.auth.models.User')
    >>> U = get_model('user')
    >>> print print_model(U, skipblank=True)
    CREATE TABLE user (year INTEGER, "group" INTEGER, id INTEGER NOT NULL, PRIMARY KEY (id));CREATE UNIQUE INDEX user_idx ON "user" (year);
    """

def test_model_config():
    """
    >>> app = make_simple_application(project_dir='.', reuse=False)
    >>> M = get_model('model_config')
    >>> MH = get_model('model_config_his')
    >>> fields = [
    ...     {'name':'year', 'type':'int'},
    ...     {'name':'username', 'type':'str'},
    ...     {'name':'age', 'type':'int'},
    ...     {'name':'group', 'type':'Reference', 'reference_class':'usergroup', 'collection_name':'myusers'}
    ... ]
    >>> indexes = [
    ...     {'name':'user_idx', 'fields':['year'], 'unique':True},
    ... ]
    >>> from uliweb.utils.common import get_uuid
    >>> from uliweb.utils import date
    >>> mh = MH(model_name='user', table_name='user', basemodel='Test.models.User',
    ...       fields=fields, indexes=indexes, has_extension=False,
    ...       uuid=get_uuid())
    >>> mh.save(version=True)
    True
    >>> m = M(model_name='user', uuid=mh.uuid, published_time=date.now())
    >>> m.save(version=True)
    True
    >>> from uliweb.contrib.model_config import find_model
    >>> print find_model(None, 'user')
    {'model_path': '', 'engines': ['default'], 'appname': 'uliweb.contrib.model_config'}
    >>> User = get_model('user')
    >>> User.migrate()
    >>> u = User(username='guest', age=30, year=2014)
    >>> u.save()
    True
    >>> a = User.get(1)
    >>> print repr(a)
    <User {'year':2014,'username':u'guest','age':30,'group':None,'id':1}>
    >>> fields = [
    ...     {'name':'year', 'type':'int'},
    ...     {'name':'username', 'type':'str'},
    ...     {'name':'age', 'type':'int'},
    ...     {'name':'nickname', 'type':'str'},
    ...     {'name':'group', 'type':'Reference', 'reference_class':'usergroup', 'collection_name':'myusers'}
    ... ]
    >>> mh = MH(model_name='user', table_name='user', basemodel='Test.models.User',
    ...       fields=fields, indexes=indexes, has_extension=False,
    ...       uuid=get_uuid())
    >>> mh.save(version=True)
    True
    >>> m = M.get(M.c.model_name=='user')
    >>> m.uuid = mh.uuid
    >>> m.save(version=True)
    True
    >>> fields = [
    ...     {'name':'year', 'type':'int'},
    ...     {'name':'username', 'type':'str'},
    ...     {'name':'age', 'type':'int'},
    ...     {'name':'nickname', 'type':'str'},
    ...     {'name':'group', 'type':'Reference', 'reference_class':'usergroup', 'collection_name':'myusers'}
    ... ]
    >>> mh = MH(model_name='user', table_name='user', basemodel='Test.models.User',
    ...       fields=fields, indexes=indexes, has_extension=False,
    ...       uuid=get_uuid())
    >>> mh.save(version=True)
    True
    >>> m = M.get(M.c.model_name=='user')
    >>> m.uuid = mh.uuid
    >>> m.save(version=True)
    True
    >>> M = get_model('user')
    >>> print M.properties.keys()
    ['username', 'group', 'year', 'age', 'nickname', 'id']
    """

def test_extension_model():
    """
    >>> app = make_simple_application(project_dir='.', reuse=False)
    >>> M = get_model('model_config')
    >>> MH = get_model('model_config_his')
    >>> fields = [
    ...     {'name':'year', 'type':'int'},
    ...     {'name':'username', 'type':'str'},
    ...     {'name':'age', 'type':'int'},
    ...     {'name':'group', 'type':'Reference', 'reference_class':'usergroup', 'collection_name':'myusers'}
    ... ]
    >>> indexes = [
    ...     {'name':'user_idx', 'fields':['year'], 'unique':True},
    ... ]
    >>> ext_fields = [
    ...     {'name':'skill', 'type':'int'},
    ...     {'name':'level', 'type':'int'},
    ... ]
    >>> ext_indexes = [
    ...     {'name':'user_ext_idx', 'fields':['skill']}
    ... ]
    >>> from uliweb.utils.common import get_uuid
    >>> from uliweb.utils import date
    >>> MH.remove()
    >>> mh = MH(model_name='user', table_name='user', basemodel='Test.models.User',
    ...       fields=fields, indexes=indexes, has_extension=True,
    ...       extension_fields=ext_fields, extension_indexes=ext_indexes,
    ...       uuid=get_uuid())
    >>> mh.save(version=True)
    True
    >>> M.remove()
    >>> m = M(model_name='user', uuid=mh.uuid, published_time=date.now())
    >>> m.save(version=True)
    True
    >>> from uliweb.contrib.model_config import find_model
    >>> print find_model(None, 'user')
    {'model_path': '', 'engines': ['default'], 'appname': 'uliweb.contrib.model_config'}
    >>> User = get_model('user')
    >>> User.remove()
    >>> User.migrate()
    >>> User.ext._model.migrate()
    >>> User.ext._model.remove()
    >>> u = User(username='guest', age=30, year=2014)
    >>> u.save()
    True
    >>> u.ext.skill = 2
    >>> u.ext.level = 3
    >>> u.ext.save()
    True
    >>> a = User.get(1)
    >>> print repr(a)
    <User {'year':2014,'username':u'guest','age':30,'group':None,'id':1}>
    >>> print repr(a.ext)
    <User_Extension {'_parent':<OneToOne:1>,'skill':2,'level':3,'id':1}>
    >>> fields = [
    ...     {'name':'year', 'type':'int'},
    ...     {'name':'username', 'type':'str'},
    ...     {'name':'age', 'type':'int'},
    ...     {'name':'nickname', 'type':'str'},
    ...     {'name':'group', 'type':'Reference', 'reference_class':'usergroup', 'collection_name':'myusers'}
    ... ]
    >>> mh = MH(model_name='user', table_name='user', basemodel='Test.models.User',
    ...       fields=fields, indexes=indexes, has_extension=False,
    ...       uuid=get_uuid())
    >>> mh.save(version=True)
    True
    >>> m = M.get(M.c.model_name=='user')
    >>> m.uuid = mh.uuid
    >>> m.save(version=True)
    True
    >>> M = get_model('user')
    >>> print M.properties.keys()
    ['username', 'group', 'year', 'age', 'nickname', 'id']
    """

def test_model_config_app():
    """
    >>> app = make_simple_application(project_dir='.', reuse=False)
    >>> M = get_model('model_config')
    >>> MH = get_model('model_config_his')
    >>> fields = [
    ...     {'name':'year', 'type':'int'},
    ...     {'name':'username', 'type':'str'},
    ...     {'name':'age', 'type':'int'},
    ...     {'name':'group', 'type':'Reference', 'reference_class':'usergroup', 'collection_name':'myusers'}
    ... ]
    >>> indexes = [
    ...     {'name':'user_idx', 'fields':['year'], 'unique':True},
    ... ]
    >>> ext_fields = [
    ...     {'name':'skill', 'type':'int'},
    ...     {'name':'level', 'type':'int'},
    ... ]
    >>> ext_indexes = [
    ...     {'name':'user_ext_idx', 'fields':['skill']},
    ... ]
    >>> from uliweb.utils.common import get_uuid
    >>> from uliweb.utils import date
    >>> MH.remove()
    >>> mh = MH(model_name='user', table_name='user', basemodel='Test.models.User',
    ...       fields=fields, indexes=indexes, has_extension=True,
    ...       extension_fields=ext_fields, extension_indexes=ext_indexes,
    ...       uuid=get_uuid())
    >>> mh.save(version=True)
    True
    >>> M.remove()
    >>> m = M(model_name='user', uuid=mh.uuid, published_time=date.now())
    >>> m.save(version=True)
    True
    >>> from uliweb.contrib.orm.commands import get_tables
    >>> tables = []
    >>> for name, t in get_tables('.').items():
    ...     tables.append((name, t.__mapping_only__))
    >>> print tables
    [('model_config_his', False), ('user1', False), ('model_config', False), ('user_extension', True), ('user', True), ('usergroup', False)]
    >>> tables = []
    >>> for name, t in get_metadata().tables.items():
    ...     tables.append((name, t.__mapping_only__))
    >>> print tables
    [('model_config_his', False), ('user1', False), ('model_config', False), ('user_extension', True), ('user', True), ('usergroup', False)]
    >>> manage.call('uliweb syncdb -v')
    Connection [Engine:default]:sqlite:///database.db
    <BLANKLINE>
    [default] Creating [1/6, uliweb] model_config_his...EXISTED
    [default] Creating [2/6, uliweb] user1...EXISTED
    [default] Creating [3/6, uliweb] model_config...EXISTED
    [default] Creating [4/6, uliweb] user_extension...SKIPPED(Mapping Table)
    [default] Creating [5/6, uliweb] user...SKIPPED(Mapping Table)
    [default] Creating [6/6, uliweb] usergroup...EXISTED
    """


# app = make_simple_application(project_dir='.', reuse=False)
# set_echo(True)
# M = get_model('model_config')
# MH = get_model('model_config_his')
# fields = [
#     ('year', 'int'),
#     ('username', 'str'),
#     ('age', 'int'),
#     ('group', 'Reference', {'reference_class':'usergroup', 'collection_name':'myusers'})
# ]
# indexes = [
#     ('user_idx', ['year'], {'unique':True})
# ]
# ext_fields = [
#     ('skill', 'int'),
#     ('level', 'int'),
# ]
# ext_indexes = [
#     ('user_ext_idx', ['skill'])
# ]
# from uliweb.utils.common import get_uuid
# from uliweb.utils import date
# MH.remove()
# mh = MH(model_name='user', table_name='user', basemodel='Test.models.User',
#       fields=fields, indexes=indexes, has_extension=True,
#       extension_fields=ext_fields, extension_indexes=ext_indexes,
#       uuid=get_uuid())
# mh.save(version=True)
#
# M.remove()
# m = M(name='user', cur_uuid=mh.uuid, submitted_time=date.now())
# m.save(version=True)
# from uliweb.contrib.orm.commands import get_tables
#
# tables = []
# for name, t in get_tables('.').items():
#     tables.append((name, t.__mapping_only__))
# print tables
#
# tables = []
# for name, t in get_metadata().tables.items():
#     tables.append((name, t.__mapping_only__))
# print tables
# manage.call('uliweb syncdb -v')

