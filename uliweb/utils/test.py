import os, sys
import uliweb

lib_path = os.path.join(uliweb.__path__[0], 'lib')
sys.path.insert(0, lib_path)

def get_app(project_path='.', settings_file='settings.ini', local_settings_file='local_settings.ini'):
    from uliweb.manage import make_application
    
    app = make_application(project_dir=project_path, start=False)
    return app

def client(project_path='.', settings_file='settings.ini', local_settings_file='local_settings.ini'):
    from werkzeug.test import Client
    from werkzeug.wrappers import Response
    
    os.chdir(project_path)
    app = get_app(project_path, settings_file, local_settings_file)
    c = Client(app, Response)
    c.app = app
    return c
