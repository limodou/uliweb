from uliweb.core.dispatch import bind
from uliweb.core.SimpleFrame import expose

@bind('startup_installed')
def startup_installed(sender):
    url = sender.settings.wsgi_middleware_staticfiles.STATIC_URL.rstrip('/')
    expose('%s/<path:filename>' % url, static=True)(static)
    
@bind('prepare_default_env')
def prepare_default_env(sender, env):
    env['url_for_static'] = url_for_static
    
def url_for_static(filename=None, **kwargs):
    from uliweb import url_for
    from urlparse import urlparse
    
    if filename.startswith('/'):
        return filename
    r = urlparse(filename)
    if r.scheme or r.netloc:
        return filename
    kwargs['filename'] = filename
    return url_for('uliweb.contrib.staticfiles.static', **kwargs)

def static(filename):
    pass

