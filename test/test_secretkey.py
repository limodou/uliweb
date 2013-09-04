import time, sys, os
path = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, path)
from uliweb import manage, functions

def teardown():
    import shutil
    os.chdir('..')
    if os.path.exists('TestProject'):
        shutil.rmtree('TestProject', ignore_errors=True)

def test_file():
    """
    >>> teardown()
    >>> from uliweb.utils.pyini import Ini
    >>> manage.call('uliweb makeproject -f TestProject')
    >>> os.chdir('TestProject')
    >>> path = os.getcwd()
    >>> ini = Ini('apps/settings.ini')
    >>> ini.GLOBAL.INSTALLED_APPS = ['uliweb.contrib.secretkey']
    >>> ini.save()
    >>> app = manage.make_simple_application(project_dir=path)
    >>> manage.call('uliweb makekey')
    >>> a = 'hello'
    >>> b = functions.encrypt(a)
    >>> c = functions.decrypt(b)
    >>> print c
    hello
    >>> manage.call('uliweb makekey -o other.key')
    >>> b1 = functions.encrypt(a, keyfile='other.key')
    >>> c1 = functions.decrypt(b1, keyfile='other.key')
    >>> print c1
    hello
    """

#if __name__ == '__main__':
#    from uliweb.utils.pyini import Ini
#    manage.call('uliweb makeproject -f TestProject')
#    os.chdir('TestProject')
#    path = os.getcwd()
#    ini = Ini('apps/settings.ini')
#    ini.GLOBAL.INSTALLED_APPS = ['uliweb.contrib.secretkey']
#    ini.save()
#    app = manage.make_simple_application(project_dir=path)
#    manage.call('uliweb makekey')
#    a = 'hello'
#    b = functions.encrypt(a)
#    c = functions.decrypt(b)
#    print c
#    manage.call('uliweb makekey -o other.key')
#    b1 = functions.encrypt(a, keyfile='other.key')
#    c1 = functions.decrypt(b1, keyfile='other.key')
#    print c1
