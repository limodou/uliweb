import os
from uliweb import manage
from uliweb.orm import *
from uliweb.manage import make_simple_application

os.chdir('test_multidb')

manage.call('uliweb syncdb')
manage.call('uliweb syncdb --engine=b')

def test_is_in_web():
    """
    >>> app = make_simple_application(project_dir='.')
    >>> from uliweb import is_in_web
    >>> print is_in_web()
    False
    >>> from uliweb.utils.test import client
    >>> c = client('.')
    >>> r = c.get('/test_web')
    >>> print r.data
    True
    """
    
