####################################################################
# Author: Limodou@gmail.com
# License: BSD
####################################################################

__author__ = 'limodou'
__author_email__ = 'limodou@gmail.com'
__url__ = 'https://github.com/limodou/uliweb'
__license__ = 'BSD'
version = __version__ = '0.1.3'

import os, sys
workpath = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(workpath, 'lib'))

class UliwebError(Exception): pass

from uliweb.core.SimpleFrame import (Request, Response, redirect, Redirect, error, json, 
        POST, GET, url_for, expose, get_app_dir, get_apps, function, decorators,
        functions, response, request, settings, application, NotFound, HTTPException,
    )
from uliweb.core.js import json_dumps
from uliweb.core.storage import Storage

class Middleware(object):
    ORDER = 500
    
    def __init__(self, application, settings):
        self.application = application
        self.settings = settings
        