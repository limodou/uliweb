import time, sys, os
path = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, path)
from uliweb import manage, functions
from uliweb.contrib.objcache import *

def setup():
    import shutil
    if os.path.exists('TestProject'):
        shutil.rmtree('TestProject', ignore_errors=True)
    
def teardown():
    import shutil
    os.chdir('..')
    if os.path.exists('TestProject'):
        shutil.rmtree('TestProject', ignore_errors=True)

def test_file():
    """
    >>> init()
    [default] Creating [1/5, Test] blog...CREATED
    [default] Creating [2/5, Test] group_user_members...CREATED
    [default] Creating [3/5, Test] group...CREATED
    [default] Creating [4/5, Test] user...CREATED
    [default] Creating [5/5, uliweb.contrib.tables] tables...CREATED
    >>> User = functions.get_model('user')
    >>> Group = functions.get_model('group')
    >>> a = User(username='limodou', email='limodou@abc.om')
    >>> a.save()
    True
    >>> b = User(username='test', email='test@abc.com')
    >>> b.save()
    True
    >>> g = Group(name='python', manager=a, members=[a, b])
    >>> g.save()
    True
    >>> ca = User.get(a.id, cache=True)
    >>> print ca.username, ca.email
    limodou limodou@abc.om
    >>> redis = functions.get_redis()
    >>> _id = get_id('default', 'user', a.id)
    >>> redis.hgetall(_id)
    {'username': 'limodou', 'email': 'limodou@abc.om', 'id': '1'}
    >>> gc = Group.get(g.id, cache=True)
    >>> gc.name
    u'python'
    >>> Blog = functions.get_model('blog')
    >>> b = Blog(sid='abc', subject='123')
    >>> b.save()
    True
    >>> c = Blog(sid='ccc', subject='456')
    >>> c.save()
    True
    >>> functions.get_cached_object('blog', 'abc', condition=Blog.c.sid=='abc')
    <Blog {'sid':u'abc','subject':u'123','id':1}>
    >>> _id = get_id('default', 'blog', 'abc')
    >>> _id
    'OC:default:3:abc'
    >>> redis.hgetall(_id)
    {'sid': 'abc', 'id': '1', 'subject': '123'}
    >>> redis.delete(_id)
    1
    >>> functions.get_cached_object('blog', 'abc', condition=Blog.c.sid=='abc')
    <Blog {'sid':u'abc','subject':u'123','id':1}>
    >>> redis.hgetall(_id)
    {}
    >>> print clear_table('default', 'blog')
    1
    >>> #functions.get_cached_object('blog', 'abc', condition=Blog.c.sid=='abc')
    <Blog {'sid':u'abc','subject':u'123','id':1}>
    >>> teardown()
    """

def init():
    setup()
    manage.call('uliweb makeproject --yes TestProject')
    os.chdir('TestProject')
    path = os.getcwd()
    manage.call('uliweb makeapp Test')
    f = open('apps/Test/models.py', 'w')
    f.write('''
from uliweb.orm import *

class User(Model):
    username = Field(str)
    birth = Field(datetime.date)
    email =Field(str)
    
class Group(Model):
    name = Field(str)
    members = ManyToMany('user')
    manager = Reference('user')
    
class Blog(Model):
    sid = Field(str)
    subject = Field(str)
''')
    f.close()
    f = open('apps/settings.ini', 'w')
    f.write('''
[GLOBAL]
INSTALLED_APPS = [
'uliweb.contrib.redis_cli', 
'uliweb.contrib.orm', 
'uliweb.contrib.objcache', 
'Test'
]

[LOG]
level = 'info'

[LOG.Loggers]
uliweb.contrib.objcache = {'level':'info'}

[MODELS]
user = 'Test.models.User'
group = 'Test.models.Group'
blog = 'Test.models.Blog'

[OBJCACHE_TABLES]
user = 'username', 'email'
group = 'name'
blog = {'key':'sid'}
''')
    f.close()
    manage.call('uliweb syncdb')
    app = manage.make_simple_application(project_dir=path)

if __name__ == '__main__':
    init()
#    User = functions.get_model('user')
#    Group = functions.get_model('group')
#    a = User(username='limodou', email='limodou@abc.om')
#    a.save()
#    b = User(username='test', email='test@abc.com')
#    b.save()
#    g = Group(name='python', manager=a, members=[a, b])
#    g.save()
#    ca = User.get(a.id, cache=True)
#    print "user=", ca.username, ca.email
#    redis = functions.get_redis()
#    print "redis user=", redis.hgetall('objcache:user:%d' % a.id)
#    gc = Group.get(g.id, cache=True)
#    print "group=", gc.name
#    print "group.manager=", repr(gc.manager)
#    gd = Group.get(g.id, cache=True)
#    teardown()