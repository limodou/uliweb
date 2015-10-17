#coding=utf-8
import time, sys
sys.path.insert(0, '../uliweb/lib')
from uliweb.orm import *
import uliweb
import uliweb.orm
uliweb.orm.__auto_create__ = True
uliweb.orm.__nullable__ = True
uliweb.orm.__server_default__ = False
import mock
from uliweb.utils.generic import QueryView, ListView

class Request(object):
    values = {'page':1, 'rows':10, 'limit':10}
    GET = {}

    def __init__(self):
        self.query_string = ''
        self.path = ''

class Functions(object):
    def get_model(self, name):
        return get_model(name)
    QueryView = QueryView
    ListView = ListView

functions = mock.Mock(return_value=Functions())
uliweb.functions = functions()

from uliweb.contrib.generic import MultiView

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
    >>> request = mock.Mock(return_value=Request())
    >>> uliweb.request = request()
    >>> view = ListView(Test, group_by=Test.c.username)
    >>> query = view.query()
    >>> print str(query.get_query()).replace('\\n', ' ')
    SELECT test.username, test.year, test.birth, test.id  FROM test  WHERE 1 = 1 GROUP BY test.username  LIMIT ? OFFSET ?
    >>> # set_echo(True)
    >>> print query.count()
    1
    """

def test_multi_view_basic():
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
    >>> class MyView(MultiView):
    ...     _model = 'test'
    >>> view = MyView()
    >>> fields = [
    ... {'name':'username'}
    ... ]
    >>> c = {'username':'guest'}
    >>> print str(view._get_query_condition(Test, fields=fields, values=c))
    test.username = :username_1
    >>> fields = [
    ... {'name':'username', 'like':'%_%'},
    ... {'name':'year', 'op':'ge'}
    ... ]
    >>> print rawsql(view._get_query_condition(Test, fields=fields, values=c))
    test.username LIKE '%guest%'
    >>> c = {'username':'guest', 'year':30}
    >>> print rawsql(view._get_query_condition(Test, fields=fields, values=c))
    test.year >= 30 AND test.username LIKE '%guest%'
    """

def test_multi_view_basic():
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
    >>> class MyView(MultiView):
    ...     _model = 'test'
    >>> view = MyView()
    >>> view._list() # doctest:+ELLIPSIS
    {'page_rows': 10, 'query_form': <uliweb.utils.generic.DummyForm object at ...>, 'limit': 10, 'pageno': 1, 'table': <uliweb.utils.generic.ListView object at ...>, 'total': 0, 'table_id': 'listview_table', 'page': 1}
    """