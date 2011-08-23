import os, sys
import uliweb

lib_path = os.path.join(uliweb.__path__[0], 'lib')
sys.path.insert(0, lib_path)

def get_app(project_path='.'):
    from uliweb.manage import make_application
    
    app = make_application(apps_dir='apps', start=False)
    return app

def client(project_path='.'):
    from werkzeug.test import Client
    from werkzeug.wrappers import Response
    
    os.chdir(project_path)
    app = get_app(project_path)
    c = Client(app, Response)
    c.app = app
    return c
