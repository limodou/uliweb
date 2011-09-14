#coding=utf-8
import time, sys
sys.path.insert(0, '../uliweb/lib')
from uliweb.orm import *

#basic testing
def test_1():
    """
    >>> db = get_connection('sqlite://')
    >>> db.metadata.drop_all()
    >>> class Test(Model):
    ...     username = Field(unicode)
    ...     year = Field(int, default=0)
    ...     birth = Field(datetime.date)
    >>> a = Test(username='limodou', birth='2011-03-04')
    >>> a.save()
    True
    >>> a
    <Test {'username':u'limodou','year':0,'birth':datetime.date(2011, 3, 4),'id':1}>
    >>> b = Test(username=u'limodou1')
    >>> b.save()
    True
    >>> b
    <Test {'username':u'limodou1','year':0,'birth':None,'id':2}>
    >>> print list(Test.all())
    [<Test {'username':u'limodou','year':0,'birth':datetime.date(2011, 3, 4),'id':1}>, <Test {'username':u'limodou1','year':0,'birth':None,'id':2}>]
    >>> print Test.count()
    2
    >>> a.username
    u'limodou'
    >>> list(Test.filter(Test.c.username==u'limodou'))
    [<Test {'username':u'limodou','year':0,'birth':datetime.date(2011, 3, 4),'id':1}>]
    >>> c = Test.get(1)
    >>> c
    <Test {'username':u'limodou','year':0,'birth':datetime.date(2011, 3, 4),'id':1}>
    >>> c = Test.get(Test.c.id==1)
    >>> c
    <Test {'username':u'limodou','year':0,'birth':datetime.date(2011, 3, 4),'id':1}>
    >>> Test.remove(1)
    >>> Test.count()
    1
    >>> Test.remove([3,4,5])
    >>> Test.count()
    1
    >>> Test.remove(Test.c.id==2)
    >>> Test.count()
    0
    >>> a = Test(username='tttt')
    >>> a.save()
    True
    """
    
#testing model alter one the fly
def test_2():
    """
    >>> db = get_connection('sqlite://')
    >>> db.metadata.drop_all()
    >>> class Test(Model):
    ...     username = Field(str)
    ...     year = Field(int)
    ...     name = Field(str, max_length=65536)
    >>> class Test(Model):
    ...     username = Field(str, max_length=20)
    ...     year = Field(int)
    >>> Test.table.columns.keys()
    ['username', 'id', 'year']
    """
    
#testing many2one
def test_3():
    """
    >>> db = get_connection('sqlite://')
    >>> db.metadata.drop_all()
    >>> class Test(Model):
    ...     username = Field(str)
    ...     year = Field(int)
    >>> class Test1(Model):
    ...     test1 = Reference(Test, collection_name='test1')
    ...     test2 = Reference(Test, collection_name='test2')
    ...     name = Field(str)
    >>> a1 = Test(username='limodou1')
    >>> a1.save()
    True
    >>> a2 = Test(username='limodou2')
    >>> a2.save()
    True
    >>> a3 = Test(username='limodou3')
    >>> a3.save()
    True
    >>> b1 = Test1(name='user', test1=a1, test2=a1)
    >>> b1.save()
    True
    >>> b2 = Test1(name='aaaa', test1=a1, test2=a2)
    >>> b2.save()
    True
    >>> b3 = Test1(name='bbbb', test1=a2, test2=a3)
    >>> b3.save()
    True
    >>> a1
    <Test {'username':u'limodou1','year':0,'id':1}>
    >>> list(a1.test1.all())[0]
    <Test1 {'test1':<Test {'username':u'limodou1','year':0,'id':1}>,'test2':<Test {'username':u'limodou1','year':0,'id':1}>,'name':u'user','id':1}>
    >>> a1.test1.count()
    2
    >>> list(a2.test2.all())
    [<Test1 {'test1':<Test {'username':u'limodou1','year':0,'id':1}>,'test2':<Test {'username':u'limodou2','year':0,'id':2}>,'name':u'aaaa','id':2}>]
    >>> list(a1.test1.filter(Test1.c.name=='user'))
    [<Test1 {'test1':<Test {'username':u'limodou1','year':0,'id':1}>,'test2':<Test {'username':u'limodou1','year':0,'id':1}>,'name':u'user','id':1}>]
    >>> b1.test1
    <Test {'username':u'limodou1','year':0,'id':1}>
    >>> a1.username = 'user'
    >>> Test.get(1)
    <Test {'username':u'limodou1','year':0,'id':1}>
    >>> x = a1.save()
    >>> Test.get(1)
    <Test {'username':u'user','year':0,'id':1}>
    """
    
#testing many2one using collection_name
def test_4():
    """
    >>> db = get_connection('sqlite://')
    >>> db.metadata.drop_all()
    >>> class Test(Model):
    ...     username = Field(str)
    ...     year = Field(int)
    >>> class Test1(Model):
    ...     test = Reference(Test, collection_name='tttt')
    ...     name = Field(str)
    >>> a1 = Test(username='limodou1')
    >>> a1.save()
    True
    >>> b1 = Test1(name='user', test=a1)
    >>> b1.save()
    True
    >>> b2 = Test1(name='aaaa', test=a1)
    >>> b2.save()
    True
    >>> a1
    <Test {'username':u'limodou1','year':0,'id':1}>
    >>> list(a1.tttt.all())[0]   #here we use tttt but not test1_set
    <Test1 {'test':<Test {'username':u'limodou1','year':0,'id':1}>,'name':u'user','id':1}>
    >>> a1.tttt.count()
    2
    >>> b3 = Test1(name='aaaa')
    >>> b3.save()
    True
    >>> a1.tttt.count()
    2
    >>> b3.test = a1
    >>> b3.save()
    True
    >>> b3
    <Test1 {'test':<Test {'username':u'limodou1','year':0,'id':1}>,'name':u'aaaa','id':3}>
    >>> Test1.get(3)
    <Test1 {'test':<Test {'username':u'limodou1','year':0,'id':1}>,'name':u'aaaa','id':3}>
    """
    
#testing transaction
def test_5():
    """
    >>> db = get_connection('sqlite://')
    >>> db.metadata.drop_all()
    >>> class Test(Model):
    ...     username = Field(unicode)
    ...     year = Field(int, default=0)
    >>> t = db.begin()
    >>> a = Test(username='limodou').save()
    >>> b = Test(username='limodou').save()
    >>> db.rollback()
    >>> Test.count()
    0
    >>> t = db.begin()
    >>> a = Test(username='limodou').save()
    >>> b = Test(username='limodou').save()
    >>> db.commit()
    >>> Test.count()
    2
    """
  
#testing OneToOne
def test_6():
    """
    >>> db = get_connection('sqlite://')
    >>> db.metadata.drop_all()
    >>> class Test(Model):
    ...     username = Field(str)
    ...     year = Field(int)
    >>> class Test1(Model):
    ...     test = OneToOne(Test)
    ...     name = Field(str)
    >>> a1 = Test(username='limodou1')
    >>> a1.save()
    True
    >>> b1 = Test1(name='user', test=a1)
    >>> b1.save()
    True
    >>> a1
    <Test {'username':u'limodou1','year':0,'id':1}>
    >>> a1.test1
    <Test1 {'test':<Test {'username':u'limodou1','year':0,'id':1}>,'name':u'user','id':1}>
    >>> b1.test
    <Test {'username':u'limodou1','year':0,'id':1}>
    """
    
#test ManyToMany
def test_7():
    """
    >>> set_debug_query(True)
    >>> db = get_connection('sqlite://')
    >>> db.metadata.drop_all()
    >>> class User(Model):
    ...     username = Field(unicode)
    >>> class Group(Model):
    ...     name = Field(str)
    ...     users = ManyToMany(User)
    >>> a = User(username='limodou')
    >>> a.save()
    True
    >>> b = User(username='user')
    >>> b.save()
    True
    >>> c = User(username='abc')
    >>> c.save()
    True
    >>> g1 = Group(name='python')
    >>> g1.save()
    True
    >>> g2 = Group(name='perl')
    >>> g2.save()
    True
    >>> g3 = Group(name='java')
    >>> g3.save()
    True
    >>> g1.users.add(a)
    True
    >>> g1.users.add(b, 3) #add can support multiple object, and object can also int
    True
    >>> g1.users.add(a, b)  #can has duplicated records
    False
    >>> list(g1.users.all())
    [<User {'username':u'limodou','id':1}>, <User {'username':u'user','id':2}>, <User {'username':u'abc','id':3}>]
    >>> g1.users.clear(a)
    >>> g1.users.clear()
    >>> g1.users.count()
    0
    >>> g1.users.add(a, b, c)
    True
    >>> g1.users.add([a, b, c])
    False
    >>> g1.to_dict()
    {'id': 1, 'name': 'python'}
    >>> g1.to_dict(manytomany=True)
    {'users': [1, 2, 3], 'id': 1, 'name': 'python'}
    >>> g1.users.count()
    3
    >>> g1.users.has(a)
    True
    >>> g1.users.has(100)
    False
    >>> g2.users.add(a)
    True
    >>> list(a.group_set.all())
    [<Group {'name':u'python','id':1}>, <Group {'name':u'perl','id':2}>]
    >>> a.group_set.add(g3)
    True
    >>> list(a.group_set.all())
    [<Group {'name':u'python','id':1}>, <Group {'name':u'perl','id':2}>, <Group {'name':u'java','id':3}>]
    >>> g1.users.clear(a)
    >>> list(g1.users.all())
    [<User {'username':u'user','id':2}>, <User {'username':u'abc','id':3}>]
    >>> list(g2.users.all())
    [<User {'username':u'limodou','id':1}>]
    >>> list(a.group_set.all())
    [<Group {'name':u'perl','id':2}>, <Group {'name':u'java','id':3}>]
    >>> g1.users.get(2)
    <User {'username':u'user','id':2}>
    >>> list(g1.users.filter(User.c.id==3).all())
    [<User {'username':u'abc','id':3}>]
    >>> g2.users.add(c)
    True
    >>> list(Group.filter(Group.users.in_(3)))
    [<Group {'name':u'python','id':1}>, <Group {'name':u'perl','id':2}>]
    >>> g1.update(users=[1,2])
    <Group {'name':u'python','id':1}>
    >>> g1.save()
    True
    >>> g1.to_dict(manytomany=True)
    {'users': [1, 2], 'id': 1, 'name': 'python'}
    """

#test SelfReference
def test_8():
    """
    >>> set_debug_query(True)
    >>> db = get_connection('sqlite://')
    >>> db.metadata.drop_all()
    >>> class User(Model):
    ...     username = Field(unicode)
    ...     parent = SelfReference(collection_name='children')
    >>> a = User(username='a')
    >>> a.save()
    True
    >>> b = User(username='b', parent=a)
    >>> b.save()
    True
    >>> c = User(username='c', parent=a)
    >>> c.save()
    True
    >>> for i in User.all():
    ...     print repr(i)
    <User {'username':u'a','parent':None,'id':1}>
    <User {'username':u'b','parent':<User {'username':u'a','parent':None,'id':1}>,'id':2}>
    <User {'username':u'c','parent':<User {'username':u'a','parent':None,'id':1}>,'id':3}>
    >>> for i in a.children.all():
    ...     print repr(i)
    <User {'username':u'b','parent':<User {'username':u'a','parent':None,'id':1}>,'id':2}>
    <User {'username':u'c','parent':<User {'username':u'a','parent':None,'id':1}>,'id':3}>
    """
    
def test_floatproperty():
    """
    >>> db = get_connection('sqlite://')
    >>> db.metadata.drop_all()
    >>> class Test1(Model):
    ...     f = FloatProperty(precision=6)
    >>> Test1.f.precision
    6
    >>> a = Test1(f=23.123456789)
    >>> a.save()
    True
    >>> a
    <Test1 {'f':23.123456788999999,'id':1}>
    >>> Test1.get(1)
    <Test1 {'f':23.123456788999999,'id':1}>
    >>> a.f = 0.000000001 #test float zero
    >>> a.f
    0.0
    """
    
def test_datetime_property():
    """
    >>> db = get_connection('sqlite://')
    >>> db.metadata.drop_all()
    >>> class Test(Model):
    ...     date1 = DateTimeProperty()
    ...     date2 = DateProperty()
    ...     date3 = TimeProperty()
    >>> a = Test()
    >>> #test common datetime object
    >>> a.date1 = None
    >>> a.date1=datetime.datetime(2009,1,1,14,0,5)
    >>> a.date2=datetime.date(2009,1,1)
    >>> a.date3=datetime.time(14,0,5)
    >>> #test to_dict function
    >>> print a.to_dict()
    {'date1': '2009-01-01 14:00:05', 'date3': '14:00:05', 'date2': '2009-01-01', 'id': None}
    >>> print a.to_dict(fields=('date1', 'date2'))
    {'date1': '2009-01-01 14:00:05', 'date2': '2009-01-01'}
    >>> print repr(a.date1)
    datetime.datetime(2009, 1, 1, 14, 0, 5)
    >>> print repr(a.date2)
    datetime.date(2009, 1, 1)
    >>> print repr(a.date3)
    datetime.time(14, 0, 5)
    >>> #test saving result
    >>> a.save()
    True
    >>> a
    <Test {'date1':datetime.datetime(2009, 1, 1, 14, 0, 5),'date2':datetime.date(2009, 1, 1),'date3':datetime.time(14, 0, 5),'id':1}>
    >>> #test to_dict function
    >>> print a.to_dict()
    {'date1': '2009-01-01 14:00:05', 'date3': '14:00:05', 'date2': '2009-01-01', 'id': 1}
    >>> #test different datetime object to diffent datetime property
    >>> a.date2=datetime.datetime(2009,1,1,14,0,5)
    >>> a.date3=datetime.datetime(2009,1,1,14,0,5)
    >>> print repr(a.date2)
    datetime.date(2009, 1, 1)
    >>> print repr(a.date3)
    datetime.time(14, 0, 5)
    >>> #test string format to datetime property
    >>> a.date1 = '2009-01-01 14:00:05'
    >>> a.date2 = '2009-01-01'
    >>> a.date3 = '14:00:05'
    >>> print repr(a.date1)
    datetime.datetime(2009, 1, 1, 14, 0, 5)
    >>> print repr(a.date2)
    datetime.date(2009, 1, 1)
    >>> print repr(a.date3)
    datetime.time(14, 0, 5)
    >>> #test different string format to datetime property
    >>> a.date1 = '2009/01/01 14:00:05'
    >>> a.date2 = '2009-01-01 14:00:05'
    >>> a.date3 = '2009-01-01 14:00:05'
    >>> print repr(a.date1)
    datetime.datetime(2009, 1, 1, 14, 0, 5)
    >>> print repr(a.date2)
    datetime.date(2009, 1, 1)
    >>> print repr(a.date3)
    datetime.time(14, 0, 5)
    """
    
def test_to_dict():
    """
    >>> set_debug_query(True)
    >>> db = get_connection('sqlite://')
    >>> db.metadata.drop_all()
    >>> import datetime
    >>> class Test(Model):
    ...     string = StringProperty(max_length=40)
    ...     boolean = BooleanProperty()
    ...     integer = IntegerProperty()
    ...     date1 = DateTimeProperty()
    ...     date2 = DateProperty()
    ...     date3 = TimeProperty()
    ...     float = FloatProperty()
    ...     decimal = DecimalProperty()
    >>> a = Test()
    >>> a.date1=datetime.datetime(2009,1,1,14,0,5)
    >>> a.date2=datetime.date(2009,1,1)
    >>> a.date3=datetime.time(14,0,0)
    >>> a.string = 'limodou'
    >>> a.boolean = True
    >>> a.integer = 200
    >>> a.float = 200.02
    >>> a.decimal = decimal.Decimal("10.2")
    >>> a.to_dict()
    {'date1': '2009-01-01 14:00:05', 'date3': '14:00:00', 'date2': '2009-01-01', 'string': 'limodou', 'decimal': '10.2', 'float': 200.02000000000001, 'boolean': True, 'integer': 200, 'id': None}
    >>> a.save()
    True
    >>> a
    <Test {'string':u'limodou','boolean':True,'integer':200,'date1':datetime.datetime(2009, 1, 1, 14, 0, 5),'date2':datetime.date(2009, 1, 1),'date3':datetime.time(14, 0),'float':200.02000000000001,'decimal':Decimal('10.2'),'id':1}>
    >>> a.to_dict()
    {'date1': '2009-01-01 14:00:05', 'date3': '14:00:00', 'date2': '2009-01-01', 'string': 'limodou', 'decimal': '10.2', 'float': 200.02000000000001, 'boolean': True, 'integer': 200, 'id': 1}
    """
    
def test_match():
    """
    >>> set_debug_query(False)
    >>> db = get_connection('sqlite://')
    >>> db.metadata.drop_all()
    >>> c = ['abc', 'def']
    >>> class Test(Model):
    ...     string = StringProperty(max_length=40, choices=c)
    >>> a = Test()
    >>> a #because you didn't assign a value to string, so the default will only affect at saving
    <Test {'string':u'','id':None}>
    >>> #test the correct assign
    #>>> a.string = 'abc'
    #>>> #test the error assign
    #>>> try:
    #...     a.string = 'aaa'
    #... except Exception, e:
    #...     print e
    #Property string is 'aaa'; must be one of ['abc', 'def']
    >>> #test tuple choices
    >>> c = [('abc', 'Prompt'), ('def', 'Hello')]
    >>> Test.string.choices = c
    >>> #test the correct assign
    #>>> a.string = 'abc'
    #>>> #test the error assign
    #>>> try:
    #...     a.string = 'aaa'
    #... except Exception, e:
    #...     print e
    #Property string is 'aaa'; must be one of ['abc', 'def']
    """

def test_result():
    """
    >>> db = get_connection('sqlite://')
    >>> db.echo = False
    >>> db.metadata.drop_all()
    >>> class Test(Model):
    ...     username = Field(CHAR, max_length=20)
    ...     year = Field(int, default=0)
    >>> a = Test(username='limodou', year=10)
    >>> a.save()
    True
    >>> a
    <Test {'username':u'limodou','year':10,'id':1}>
    >>> Test(username='user', year=5).save()
    True
    >>> print list(Test.all())
    [<Test {'username':u'limodou','year':10,'id':1}>, <Test {'username':u'user','year':5,'id':2}>]
    >>> print list(Test.filter(Test.c.year > 5))
    [<Test {'username':u'limodou','year':10,'id':1}>]
    >>> print list(Test.all().order_by(Test.c.year.desc()))
    [<Test {'username':u'limodou','year':10,'id':1}>, <Test {'username':u'user','year':5,'id':2}>]
    >>> print list(Test.all().order_by(Test.c.year.asc(), Test.c.username.desc()))
    [<Test {'username':u'user','year':5,'id':2}>, <Test {'username':u'limodou','year':10,'id':1}>]
    >>> print Test.count()
    2
    >>> print Test.filter(Test.c.year>5).count()
    1
    >>> print list(Test.all().values(Test.c.username, 'year'))
    [(u'limodou', 10), (u'user', 5)]
    >>> print list(Test.all().values('username'))
    [(u'limodou',), (u'user',)]
    >>> print Test.all().values_one(Test.c.username)
    (u'limodou',)
    >>> print list(Test.filter(Test.c.year<0))
    []
    >>> print Test.filter(Test.c.year<0).one()
    None
    >>> print repr(Test.filter(Test.c.year>5).one())
    <Test {'username':u'limodou','year':10,'id':1}>
    """
    
def test_save():
    """
    >>> db = get_connection('sqlite://')
    >>> db.echo = False
    >>> db.metadata.drop_all()
    >>> class Test(Model):
    ...     username = Field(CHAR, max_length=20)
    ...     year = Field(datetime.datetime, auto_now_add=True, auto_now=True)
    >>> a = Test(username='limodou')
    >>> a._get_data()
    {'username': u'limodou'}
    >>> a.save()
    True
    >>> a.to_dict() # doctest:+ELLIPSIS
    {'username': 'limodou', 'id': 1, 'year': '... ...'}
    >>> a.username = 'newuser'
    >>> a._get_data()
    {'username': u'newuser', 'id': 1}
    """
    
def test_without_id():
    """
    >>> db = get_connection('sqlite://')
    >>> db.echo = False
    >>> db.metadata.drop_all()
    >>> class Test(Model):
    ...     __without_id__ = True
    ...     username = Field(CHAR, max_length=20)
    ...     year = Field(datetime.datetime, auto_now_add=True, auto_now=True)
    >>> 'id' in Test.properties
    False
    >>> class Test(Model):
    ...     username = Field(CHAR, max_length=20)
    ...     year = Field(datetime.datetime, auto_now_add=True, auto_now=True)
    >>> 'id' in Test.properties
    True
    """
    
def test_Reference_not_int():
    """
    >>> db = get_connection('sqlite://')
    >>> db.echo = False
    >>> db.metadata.drop_all()
    >>> class Test(Model):
    ...     __without_id__ = True
    ...     username = Field(CHAR, max_length=20)
    ...     year = Field(datetime.datetime, auto_now_add=True, auto_now=True)
    >>> 'id' in Test.properties
    False
    >>> class Test(Model):
    ...     username = Field(CHAR, max_length=20)
    ...     year = Field(datetime.datetime, auto_now_add=True, auto_now=True)
    >>> 'id' in Test.properties
    True
    """
    
def test_reference_not_id():
    """
    >>> db = get_connection('sqlite://')
    >>> db.echo = False
    >>> db.metadata.drop_all()
    >>> class Test(Model):
    ...     username = Field(CHAR, max_length=20)
    ...     year = Field(int)
    >>> class Test1(Model):
    ...     test = Reference(Test, collection_name='tttt', reference_fieldname='username')
    ...     year = Field(int)
    ...     name = Field(CHAR, max_length=20)
    >>> a1 = Test(username='limodou1', year=20)
    >>> a1.save()
    True
    >>> b1 = Test1(name='user', year=5, test=a1)
    >>> b1.save()
    True
    >>> b2 = Test1(name='aaaa', year=10, test=a1)
    >>> b2.save()
    True
    >>> print repr(a1), repr(b1), repr(b2)
    <Test {'username':u'limodou1','year':20,'id':1}> <Test1 {'test':<Test {'username':u'limodou1','year':20,'id':1}>,'year':5,'name':u'user','id':1}> <Test1 {'test':<Test {'username':u'limodou1','year':20,'id':1}>,'year':10,'name':u'aaaa','id':2}>
    >>> print repr(b2.test)
    <Test {'username':u'limodou1','year':20,'id':1}>
    >>> print b2._test_
    limodou1
    >>> print a1.tttt.has(b1, b2)
    True
    >>> print a1.tttt.ids()
    [1, 2]
    >>> print list(Test1.all())
    [<Test1 {'test':<Test {'username':u'limodou1','year':20,'id':1}>,'year':5,'name':u'user','id':1}>, <Test1 {'test':<Test {'username':u'limodou1','year':20,'id':1}>,'year':10,'name':u'aaaa','id':2}>]
    >>> a1.tttt.clear(b2)
    >>> print list(Test1.all())
    [<Test1 {'test':<Test {'username':u'limodou1','year':20,'id':1}>,'year':5,'name':u'user','id':1}>]
    >>> b3 = Test1(name='aaaa', year=10, test='limodou1')
    >>> b3.save()
    True
    >>> print repr(b3)
    <Test1 {'test':<Test {'username':u'limodou1','year':20,'id':1}>,'year':10,'name':u'aaaa','id':2}>
    """

def test_one2one_reference_field():
    """
    >>> db = get_connection('sqlite://')
    >>> db.metadata.drop_all()
    >>> class Test(Model):
    ...     username = Field(str)
    ...     year = Field(int)
    >>> class Test1(Model):
    ...     test = OneToOne(Test, reference_fieldname='username')
    ...     name = Field(str)
    >>> a1 = Test(username='limodou1')
    >>> a1.save()
    True
    >>> b1 = Test1(name='user', test=a1)
    >>> b1.save()
    True
    >>> a1
    <Test {'username':u'limodou1','year':0,'id':1}>
    >>> a1.test1
    <Test1 {'test':<Test {'username':u'limodou1','year':0,'id':1}>,'name':u'user','id':1}>
    >>> b1.test
    <Test {'username':u'limodou1','year':0,'id':1}>
    """
    
def test_many2many_reference_field():
    """
    >>> db = get_connection('sqlite://')
    >>> db.echo = False
    >>> db.metadata.drop_all()
    >>> db.metadata.clear()
    >>> class User(Model):
    ...     username = Field(CHAR, max_length=20)
    ...     year = Field(int)
    >>> class Group(Model):
    ...     name = Field(str, max_length=20)
    ...     users = ManyToMany(User, reference_fieldname='username')
    >>> a = User(username='limodou', year=5)
    >>> a.save()
    True
    >>> b = User(username='user', year=10)
    >>> b.save()
    True
    >>> c = User(username='abc', year=20)
    >>> c.save()
    True
    >>> print list(User.all())
    [<User {'username':u'limodou','year':5,'id':1}>, <User {'username':u'user','year':10,'id':2}>, <User {'username':u'abc','year':20,'id':3}>]
    >>> g1 = Group(name='python')
    >>> g1.save()
    True
    >>> g2 = Group(name='perl')
    >>> g2.save()
    True
    >>> g3 = Group(name='java')
    >>> g3.save()
    True
    >>> print list(Group.all())
    [<Group {'name':u'python','id':1}>, <Group {'name':u'perl','id':2}>, <Group {'name':u'java','id':3}>]
    >>> g1.users.add(a)
    True
    >>> g1.users.add(b)
    True
    >>> g2.users.add(a)
    True
    >>> print list(g1.users.all())
    [<User {'username':u'limodou','year':5,'id':1}>, <User {'username':u'user','year':10,'id':2}>]
    >>> print list(g1.users.all().order_by(User.c.year.desc()))
    [<User {'username':u'user','year':10,'id':2}>, <User {'username':u'limodou','year':5,'id':1}>]
    >>> print list(g1.users.filter(User.c.year>5).order_by(User.c.year.desc()))
    [<User {'username':u'user','year':10,'id':2}>]
    >>> print g1.users.has(a)
    True
    >>> print list(a.group_set.all())
    [<Group {'name':u'python','id':1}>, <Group {'name':u'perl','id':2}>]
    """

def test_many2many_reference_field_and_reversed_field():
    """
    >>> db = get_connection('sqlite://')
    >>> db.echo = False
    >>> db.metadata.drop_all()
    >>> db.metadata.clear()
    >>> class User(Model):
    ...     username = Field(CHAR, max_length=20)
    ...     year = Field(int)
    >>> class Group(Model):
    ...     name = Field(str, max_length=20)
    ...     users = ManyToMany(User, reference_fieldname='username', reversed_fieldname='name')
    >>> a = User(username='limodou', year=5)
    >>> a.save()
    True
    >>> b = User(username='user', year=10)
    >>> b.save()
    True
    >>> c = User(username='abc', year=20)
    >>> c.save()
    True
    >>> print list(User.all())
    [<User {'username':u'limodou','year':5,'id':1}>, <User {'username':u'user','year':10,'id':2}>, <User {'username':u'abc','year':20,'id':3}>]
    >>> g1 = Group(name='python')
    >>> g1.save()
    True
    >>> g2 = Group(name='perl')
    >>> g2.save()
    True
    >>> g3 = Group(name='java')
    >>> g3.save()
    True
    >>> print list(Group.all())
    [<Group {'name':u'python','id':1}>, <Group {'name':u'perl','id':2}>, <Group {'name':u'java','id':3}>]
    >>> g1.users.add(a)
    True
    >>> g1.users.add(b)
    True
    >>> g2.users.add(a)
    True
    >>> print list(g1.users.all())
    [<User {'username':u'limodou','year':5,'id':1}>, <User {'username':u'user','year':10,'id':2}>]
    >>> print list(g1.users.all().order_by(User.c.year.desc()))
    [<User {'username':u'user','year':10,'id':2}>, <User {'username':u'limodou','year':5,'id':1}>]
    >>> print list(g1.users.filter(User.c.year>5).order_by(User.c.year.desc()))
    [<User {'username':u'user','year':10,'id':2}>]
    >>> print g1.users.has(a)
    True
    >>> print list(a.group_set.all())
    [<Group {'name':u'python','id':1}>, <Group {'name':u'perl','id':2}>]
    """

def test_many2many_through():
    """
    >>> db = get_connection('sqlite://')
    >>> db.echo = False
    >>> db.metadata.drop_all()
    >>> db.metadata.clear()
    >>> class User(Model):
    ...     username = Field(CHAR, max_length=20)
    ...     year = Field(int)
    >>> class Group(Model):
    ...     name = Field(str, max_length=20)
    ...     users = ManyToMany(User, through='relation')
    >>> class Relation(Model):
    ...     user = Reference(User)
    ...     group = Reference(Group)
    ...     year = Field(int)
    >>> a = User(username='limodou', year=5)
    >>> a.save()
    True
    >>> b = User(username='user', year=10)
    >>> b.save()
    True
    >>> c = User(username='abc', year=20)
    >>> c.save()
    True
    >>> print list(User.all())
    [<User {'username':u'limodou','year':5,'id':1}>, <User {'username':u'user','year':10,'id':2}>, <User {'username':u'abc','year':20,'id':3}>]
    >>> g1 = Group(name='python')
    >>> g1.save()
    True
    >>> g2 = Group(name='perl')
    >>> g2.save()
    True
    >>> g3 = Group(name='java')
    >>> g3.save()
    True
    >>> print list(Group.all())
    [<Group {'name':u'python','id':1}>, <Group {'name':u'perl','id':2}>, <Group {'name':u'java','id':3}>]
    >>> g1.users.add(a)
    True
    >>> g1.users.add(b)
    True
    >>> g2.users.add(a)
    True
    >>> print list(g1.users.all())
    [<User {'username':u'limodou','year':5,'id':1}>, <User {'username':u'user','year':10,'id':2}>]
    >>> print list(g1.users.all().order_by(User.c.year.desc()))
    [<User {'username':u'user','year':10,'id':2}>, <User {'username':u'limodou','year':5,'id':1}>]
    >>> print list(g1.users.filter(User.c.year>5).order_by(User.c.year.desc()))
    [<User {'username':u'user','year':10,'id':2}>]
    >>> print g1.users.has(a)
    True
    >>> print list(a.group_set.all())
    [<Group {'name':u'python','id':1}>, <Group {'name':u'perl','id':2}>]
    """

def test_many2many_through_alone():
    """
    >>> db = get_connection('sqlite://')
    >>> db.echo = False
    >>> db.metadata.drop_all()
    >>> db.metadata.clear()
    >>> class User(Model):
    ...     username = Field(CHAR, max_length=20)
    ...     year = Field(int)
    >>> class Group(Model):
    ...     name = Field(str, max_length=20)
    ...     users = ManyToMany(User, through='relation')
    >>> class Relation(Model):
    ...     user = Reference(User)
    ...     group = Reference(Group)
    ...     year = Field(int)
    >>> a = User(username='limodou', year=5)
    >>> a.save()
    True
    >>> b = User(username='user', year=10)
    >>> b.save()
    True
    >>> c = User(username='abc', year=20)
    >>> c.save()
    True
    >>> print list(User.all())
    [<User {'username':u'limodou','year':5,'id':1}>, <User {'username':u'user','year':10,'id':2}>, <User {'username':u'abc','year':20,'id':3}>]
    >>> g1 = Group(name='python')
    >>> g1.save()
    True
    >>> g2 = Group(name='perl')
    >>> g2.save()
    True
    >>> g3 = Group(name='java')
    >>> g3.save()
    True
    >>> print list(Group.all())
    [<Group {'name':u'python','id':1}>, <Group {'name':u'perl','id':2}>, <Group {'name':u'java','id':3}>]
    >>> r1 = Relation(user=a, group=g1, year=10)
    >>> r1.save()
    True
    >>> r2 = Relation(user=b, group=g1, year=5)
    >>> r2.save()
    True
    >>> r3 = Relation(user=a, group=g2, year=8)
    >>> r3.save()
    True
    >>> print list(g1.users.all())
    [<User {'username':u'limodou','year':5,'id':1}>, <User {'username':u'user','year':10,'id':2}>]
    >>> print list(g1.users.all().order_by(User.c.year.desc()))
    [<User {'username':u'user','year':10,'id':2}>, <User {'username':u'limodou','year':5,'id':1}>]
    >>> print list(g1.users.filter(User.c.year>5).order_by(User.c.year.desc()))
    [<User {'username':u'user','year':10,'id':2}>]
    >>> print g1.users.has(a)
    True
    >>> print list(a.group_set.all())
    [<Group {'name':u'python','id':1}>, <Group {'name':u'perl','id':2}>]
    >>> print list(g1.users.filter(Relation.c.year>5))
    [<User {'username':u'limodou','year':5,'id':1}>]
    >>> print list(a.group_set.filter(Relation.c.year>5))
    [<Group {'name':u'python','id':1}>, <Group {'name':u'perl','id':2}>]
    >>> #Test with_relation function
    >>> u = g1.users.all().with_relation().one()
    >>> print u.relation.year
    10
    """

def test_many2many_through_alone_condition():
    """
    >>> db = get_connection('sqlite://')
    >>> db.echo = False
    >>> db.metadata.drop_all()
    >>> db.metadata.clear()
    >>> class User(Model):
    ...     username = Field(CHAR, max_length=20)
    ...     year = Field(int)
    >>> class Group(Model):
    ...     name = Field(str, max_length=20)
    ...     users = ManyToMany(User, through='relation')
    >>> class Relation(Model):
    ...     user = Reference(User)
    ...     group = Reference(Group)
    ...     age = Field(int)
    >>> a = User(username='limodou', year=5)
    >>> a.save()
    True
    >>> b = User(username='user', year=10)
    >>> b.save()
    True
    >>> c = User(username='abc', year=20)
    >>> c.save()
    True
    >>> print list(User.all())
    [<User {'username':u'limodou','year':5,'id':1}>, <User {'username':u'user','year':10,'id':2}>, <User {'username':u'abc','year':20,'id':3}>]
    >>> g1 = Group(name='python')
    >>> g1.save()
    True
    >>> g2 = Group(name='perl')
    >>> g2.save()
    True
    >>> g3 = Group(name='java')
    >>> g3.save()
    True
    >>> print list(Group.all())
    [<Group {'name':u'python','id':1}>, <Group {'name':u'perl','id':2}>, <Group {'name':u'java','id':3}>]
    >>> r1 = Relation(user=a, group=g1, age=10)
    >>> r1.save()
    True
    >>> r2 = Relation(user=b, group=g1, age=5)
    >>> r2.save()
    True
    >>> r3 = Relation(user=a, group=g2, age=8)
    >>> r3.save()
    True
    >>> print list(g1.users.all())
    [<User {'username':u'limodou','year':5,'id':1}>, <User {'username':u'user','year':10,'id':2}>]
    >>> print list(g1.users.all().order_by(User.c.year.desc()))
    [<User {'username':u'user','year':10,'id':2}>, <User {'username':u'limodou','year':5,'id':1}>]
    >>> print list(g1.users.filter(User.c.year>5).order_by(User.c.year.desc()))
    [<User {'username':u'user','year':10,'id':2}>]
    >>> print g1.users.has(a)
    True
    >>> print list(a.group_set.all())
    [<Group {'name':u'python','id':1}>, <Group {'name':u'perl','id':2}>]
    >>> print list(g1.users.filter(Relation.c.age>5))
    [<User {'username':u'limodou','year':5,'id':1}>]
    >>> print list(a.group_set.filter(Relation.c.age>5))
    [<Group {'name':u'python','id':1}>, <Group {'name':u'perl','id':2}>]
    >>> print list(Group.filter(Group.users.in_(1)))
    [<Group {'name':u'python','id':1}>, <Group {'name':u'perl','id':2}>]
    >>> print list(Group.filter(Group.users.filter(User.c.username=='limodou')))
    [<Group {'name':u'python','id':1}>, <Group {'name':u'perl','id':2}>]
    >>> print list(Group.filter(Group.users.filter(User.c.username=='user')))
    [<Group {'name':u'python','id':1}>]
    
    """

def test_decimal_float():
    """
    >>> db = get_connection('sqlite://')
    >>> db.metadata.drop_all()
    >>> class Test(Model):
    ...     float = FloatProperty(precision=5)
    ...     decimal = DecimalProperty(precision=3, scale=1)
    >>> a = Test()
    >>> a.float = 200.02
    >>> a.decimal = decimal.Decimal("10.2")
    >>> a.save()
    True
    >>> a
    <Test {'float':200.02000000000001,'decimal':Decimal('10.2'),'id':1}>
    """

def test_many2many_save_and_update():
    """
    >>> db = get_connection('sqlite://')
    >>> #db.echo = True
    >>> db.metadata.drop_all()
    >>> db.metadata.clear()
    >>> class User(Model):
    ...     username = Field(CHAR, max_length=20)
    ...     year = Field(int)
    >>> class Group(Model):
    ...     name = Field(str, max_length=20)
    ...     users = ManyToMany(User, reference_fieldname='username', reversed_fieldname='name')
    >>> a = User(username='limodou', year=5)
    >>> a.save()
    True
    >>> b = User(username='test', year=3)
    >>> b.save()
    True
    >>> c = User(username='user', year=3)
    >>> c.save()
    True
    >>> g1 = Group(name='python')
    >>> g1.save()
    True
    >>> print g1.users.ids()
    []
    >>> g1.users = ['limodou', 'test']
    >>> print Group.users.get_value_for_datastore(g1, cached=True)
    ['limodou', 'test']
    >>> g1.save()
    True
    >>> print Group.users.get_value_for_datastore(g1, cached=True)
    ['limodou', 'test']
    >>> g2 = Group(name='perl', users=['user'])
    >>> g2.save()
    True
    >>> print Group.users.get_value_for_datastore(g2, cached=True)
    ['user']
    >>> g2.users = ['limodou']
    >>> g2.save()
    True
    >>> print Group.users.get_value_for_datastore(g2, cached=True)
    ['limodou']
    >>> print g2.users.ids()
    [u'limodou']
    >>> print Group.users.get_value_for_datastore(g2)
    [u'limodou']
    >>> g2.update(users=['limodou', 'test'])
    <Group {'name':u'perl','id':2}>
    >>> g2.save()
    True
    >>> print g2.users.ids()
    [u'limodou', u'test']
    >>> g2.update(name='new group', users=[])
    <Group {'name':u'new group','id':2}>
    >>> g2.save()
    True
    >>> print g2.users.ids()
    []
    """
    
def test_auto():
    """
    Test auto and auto_add parameter of property
    
    >>> db = get_connection('sqlite://')
    >>> #db.echo = True
    >>> db.metadata.drop_all()
    >>> db.metadata.clear()
    >>> class User(Model):
    ...     username = Field(CHAR, max_length=20, auto=True, auto_add=True, default='limodou')
    ...     year = Field(int)
    >>> u = User(year=10)
    >>> u.save()
    True
    >>> u
    <User {'username':u'limodou','year':10,'id':1}>
    >>> u.username = 'aaa'
    >>> u.save()
    True
    >>> u
    <User {'username':u'aaa','year':10,'id':1}>
    >>> User.username.default = 'default'
    >>> u.save()
    False
    >>> u.year = 20
    >>> u.save()
    True
    >>> u
    <User {'username':u'default','year':20,'id':1}>
    >>> class User(Model):
    ...     username = Field(CHAR, max_length=20, auto_add=True, default='limodou')
    ...     year = Field(int)
    >>> u = User(year=10)
    >>> u.save()
    True
    >>> u
    <User {'username':u'limodou','year':10,'id':2}>
    >>> u.username = 'aaa'
    >>> u.save()
    True
    >>> u
    <User {'username':u'aaa','year':10,'id':2}>
    >>> User.username.default = 'default'
    >>> u.save()
    False
    >>> u.year = 20
    >>> u.save()
    True
    >>> u
    <User {'username':u'aaa','year':20,'id':2}>
    
    """

def test_pickle():
    """
    Test auto and auto_add parameter of property
    
    >>> db = get_connection('sqlite://')
    >>> #db.echo = True
    >>> db.metadata.drop_all()
    >>> db.metadata.clear()
    >>> class User(Model):
    ...     username = Field(str, max_length=40)
    ...     memo = Field(PICKLE)
    >>> a = User(username='limodou', memo={'age':30})
    >>> a.save()
    True
    >>> print a.memo
    {'age': 30}
    >>> b = User.get(1)
    >>> print b.memo
    {'age': 30}
    """
    
#if __name__ == '__main__':
#    db = get_connection('sqlite://')
#    db.metadata.drop_all()
#    class Test(Model):
#        date1 = DateTimeProperty()
#        date2 = DateProperty()
#        date3 = TimeProperty()
#    a = Test()
#    #test common datetime object
#    a.date1 = None
#    a.date1 = datetime.datetime(2009,1,1,14,0,5)
#    
    
    
    
