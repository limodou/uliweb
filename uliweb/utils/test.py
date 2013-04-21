import os, sys
import uliweb

lib_path = os.path.join(uliweb.__path__[0], 'lib')
sys.path.insert(0, lib_path)

def get_app(project_path='.', settings_file='settings.ini', local_settings_file='local_settings.ini'):
    from uliweb.manage import make_simple_application
    
    app = make_simple_application(project_dir=project_path, settings_file=settings_file,
        local_settings_file=local_settings_file)
    return app

def client(project_path='.', settings_file='settings.ini', local_settings_file='local_settings.ini'):
    from werkzeug.test import Client
    from werkzeug.wrappers import Response
    
    app = get_app(project_path, settings_file, local_settings_file)
    c = Client(app, Response)
    c.app = app
    return c

def client_from_application(app):
    from werkzeug.test import Client
    from werkzeug.wrappers import Response
    
    c = Client(app, Response)
    c.app = app
    return c

def BlankRequest(url, **kwargs):
    from werkzeug.test import create_environ
    from uliweb import Request
    
    env = create_environ(path=url, **kwargs)
    return Request(env)
