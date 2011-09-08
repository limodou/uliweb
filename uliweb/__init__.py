####################################################################
# Author: Limodou@gmail.com
# License: BSD
####################################################################

__author__ = 'limodou'
__author_email__ = 'limodou@gmail.com'
__url__ = 'http://code.google.com/p/uliweb'
__license__ = 'BSD'
version = '0.0.1b4'

import os, sys

application = None
settings = None
static_views = []
url_map = None
local = None
apps_dir = 'apps'
project_dir = None
use_urls = False
response = None
request = None

workpath = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(workpath, 'lib'))

from uliweb.core.SimpleFrame import (Request, Response, redirect, error, json, 
        POST, GET, url_for, expose, get_app_dir, get_apps, function, decorators
    )