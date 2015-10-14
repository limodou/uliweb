#coding=utf-8
import time, sys
sys.path.insert(0, '../uliweb/lib')
from uliweb.orm import *
import uliweb.orm
uliweb.orm.__auto_create__ = True
uliweb.orm.__nullable__ = True
uliweb.orm.__server_default__ = False

class Request(object):
    values = {'page':1, 'rows':10, 'limit':10}
    GET = {}

def test_1():
    """
    >>> db = get_connection('sqlite://')
    >>> db.metadata.drop_all()
    >>> class Test(Model):
    ...     username = Field(unicode)
    ...     year = Field(int, default=30)
    ...     birth = Field(datetime.date)
    >>> a = Test(username='limodou', birth='2011-03-04')
    >>> a.save()
    True
    >>> a = Test(username='limodou', birth='2011-04-04')
    >>> a.save()
    True
    >>> from uliweb.utils.generic import ListView
    >>> import mock
    >>> request = mock.Mock(return_value=Request())
    >>> import uliweb
    >>> uliweb.request = request()
    >>> view = ListView(Test, group_by=Test.c.username)
    >>> query = view.query()
    >>> print str(query.get_query()).replace('\\n', ' ')
    SELECT test.username, test.year, test.birth, test.id  FROM test  WHERE 1 = 1 GROUP BY test.username  LIMIT ? OFFSET ?
    >>> # set_echo(True)
    >>> print query.count()
    1
    """

def test_multi_view():
    """
    >>> db = get_connection('sqlite://')
    >>> db.metadata.drop_all()
    >>> class Test(Model):
    ...     username = Field(unicode)
    ...     year = Field(int, default=30)
    ...     birth = Field(datetime.date)
    >>> a = Test(username='limodou', birth='2011-03-04')
    >>> a.save()
    True
    >>> from uliweb.utils.generic import MultiView
    >>> class MyView(MultiView):
    ...     _model = 'test'
    >>> view = MyView()
    >>> fields = [
    ... {'name':'username'}
    ... ]
    >>> c = {'username':'guest'}
    >>> print str(view._get_query_condition(Test, fields=fields, query=c))
    test.username = :username_1
    >>> fields = [
    ... {'name':'username', 'like':'%_%'},
    ... {'name':'year', 'op':'ge'}
    ... ]
    >>> print rawsql(view._get_query_condition(Test, fields=fields, query=c))
    test.username LIKE '%guest%'
    >>> c = {'username':'guest', 'year':30}
    >>> print rawsql(view._get_query_condition(Test, fields=fields, query=c))
    test.year >= 30 AND test.username LIKE '%guest%'
    """