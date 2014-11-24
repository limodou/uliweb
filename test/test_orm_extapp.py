import os
from uliweb import manage
from uliweb.orm import *
import uliweb.orm as orm
from uliweb.manage import make_simple_application

os.chdir('test_orm_ext')

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
    ...     ('year', 'int')
    ... ]
    >>> U = create_model('user2', fields)
    >>> print U.properties.keys()
    ['id', 'year']
    """

def test_dynamic_extend_model_2():
    """
    >>> app = make_simple_application(project_dir='.', reuse=False)
    >>> fields = [
    ...     ('year', 'int')
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
    ...     ('year', 'int')
    ... ]
    >>> U = create_model('user', fields, __replace__=True, basemodel='uliweb.contrib.auth.models.User')
    >>> U = get_model('user')
    >>> sql =  print_model(U, skipblank=True)
    >>> sql
    'CREATE TABLE user (year INTEGER, id INTEGER NOT NULL, PRIMARY KEY (id));'
    >>> print hasattr(U, 'check_password')
    True
    """

def test_create_model_index():
    """
    >>> app = make_simple_application(project_dir='.')
    >>> fields = [
    ...     ('year', 'int')
    ... ]
    >>> indexes = [
    ...     ('user_idx', ['year'], {'unique':True})
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
    ...     ('year', 'int'),
    ...     ('group', 'Reference', {'reference_class':'usergroup', 'collection_name':'myusers'})
    ... ]
    >>> indexes = [
    ...     ('user_idx', ['year'], {'unique':True})
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

# app = make_simple_application(project_dir='.')
# fields = [
#     ('year', 'int'),
#     ('group', 'Reference', {'reference_class':'usergroup', 'collection_name':'myusers'})
# ]
# indexes = [
#     ('user_idx', ['year'], {'unique':True})
# ]
# U = orm.create_model('user', fields, indexes=indexes,
#                      __replace__=True, basemodel='uliweb.contrib.auth.models.User')
# U = get_model('user')
# print print_model(U, skipblank=True)
#
# U = orm.create_model('user', fields, indexes=indexes,
#                      __replace__=True, basemodel='uliweb.contrib.auth.models.User')
# U = get_model('user')
# print print_model(U, skipblank=True)

# app = make_simple_application(project_dir='.', reuse=False)
# U = get_model('user')
# print U.properties.keys()
# U1 = get_model('user1')
# print U1.properties.keys()
