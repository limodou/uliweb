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
    
    setattr(Client, 'test_url', test_url)

    app = get_app(project_path, settings_file, local_settings_file)
    c = Client(app, Response)
    c.app = app
    return c

def client_from_application(app):
    from werkzeug.test import Client
    from werkzeug.wrappers import Response
    
    setattr(Client, 'test_url', test_url)

    c = Client(app, Response)
    c.app = app
    return c

def BlankRequest(url, **kwargs):
    from werkzeug.test import create_environ
    from uliweb import Request
    
    env = create_environ(path=url, **kwargs)
    return Request(env)

def test_url(self, url, data=None, method='get', ok_test=(200, 304, 302), log=True, counter=None):
    """
    Test if an url is ok
    ok_test can be tuple: it should be status_code list
        callable: then return true will be ok
    """
    if data is None:
        data = {}
    func = getattr(self, method.lower())
    r = func(url, data=data)
    
    result = False
    if isinstance(ok_test, (list, tuple)):
        result = r.status_code in ok_test
    #int,long will be treated as status code
    elif isinstance(ok_test, (int, long)):
        result = r.status_code == ok_test
    #str,unicode will be treated as text
    elif isinstance(ok_test, (str, unicode)):
        result = ok_test in r.data
    elif callable(ok_test):
        result = ok_test(url, data, method, r.status_code, r.data)    

    if counter:
        counter.add(result)
        
    flag = 'OK' if result else 'Failed'
    log_func = None
    if callable(log):
        log_func = log
    elif log is True:
        log_func = log_to_file(sys.stdout)
    elif isinstance(log, (str, unicode)):
        log_func = log_to_file(log)
    if log_func:
        log_func(url, data, method, ok_test, result, r)
    return result

def default_log(url, data, method, ok_test, result, response):
    flag = 'OK' if result else 'Failed'
    print 'Testing %s...%s' % (url, flag)
    
def log_to_file(logfile, response_text=False):
    if isinstance(logfile, (str, unicode)):
        log = open(logfile, 'a')
    else:
        log = logfile
    def _log(url, data, method, ok_test, result, response):
        flag = 'OK' if result else 'Failed'
        log.write('Testing %s...%s\n' % (url, flag))
        if not result:
            log.write('    ok_test = %s\n' % ok_test)
            log.write('    Response code=%d\n' % response.status_code)
            if response_text:
                log.write('----------------- Response Text -----------------\n')
                log.write(response.data)
                log.write('================= Response Text =================\n')
    return _log
                
class Counter(object):
    def __init__(self):
        self.total = 0
        self.passed = 0
        self.failed = 0
        
    def add(self, passed=True):
        if passed:
            self.passed +=1
        else:
            self.failed += 1
        self.total += 1