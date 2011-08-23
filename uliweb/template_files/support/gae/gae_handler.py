import os, sys
import wsgiref.handlers
from uliweb.manage import make_application

path = os.path.dirname(__file__)
if path not in sys.path:
    sys.path.insert(0, path)
apps_dir = os.path.join(path, 'apps')

application = make_application(False, apps_dir, debug_console=False)
wsgiref.handlers.CGIHandler().run(application)
