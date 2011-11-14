####################################################################
# Author: Limodou@gmail.com
# License: BSD
####################################################################

__author__ = 'limodou'
__author_email__ = 'limodou@gmail.com'
__url__ = 'http://code.google.com/p/uliweb'
__license__ = 'BSD'
version = __version__ = '0.0.1a7'

import os, sys
workpath = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(workpath, 'lib'))

class UliwebError(Exception): pass

from uliweb.core.SimpleFrame import (Request, Response, redirect, error, json, 
        POST, GET, url_for, expose, get_app_dir, get_apps, function, decorators,
        functions, response, request, settings, application, NotFound, HTTPException,
    )
from uliweb.core.js import json_dumps

class Middleware(object):
    ORDER = 500
    
    def __init__(self, application, settings):
        self.application = application
        self.settings = settings
        
#    def process_request(self, request):
#        pass
#    
#    def process_response(self, request, response):
#        pass
#    
#    def process_exception(self, request, exception):
#        pass
