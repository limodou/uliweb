import os, sys
import wsgiref.handlers
from uliweb.manage import make_application

path = os.path.dirname(__file__)
if path not in sys.path:
    sys.path.insert(0, path)

application = make_application(False, project_dir=path, debug_console=False)
wsgiref.handlers.CGIHandler().run(application)
