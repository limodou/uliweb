from uliweb.core.SimpleFrame import expose

def startup_installed(sender):
    url = sender.settings.GLOBAL.STATIC_URL.rstrip('/')
    expose('%s/<path:filename>' % url, static=True)(static)
    
def prepare_default_env(sender, env):
    env['url_for_static'] = url_for_static
    
def url_for_static(filename=None, **kwargs):
    from uliweb import settings, application
    from uliweb.core.SimpleFrame import get_url_adapter
    from urlparse import urlparse, urlunparse, urljoin
    import urllib
    
    domain = application.domains.get('static', {})

    #add STATIC_VER support
    ver = settings.GLOBAL.STATIC_VER
    if ver:
        kwargs['ver'] = ver
    
    #process external flag
    external = kwargs.pop('_external', False)
    if not external:
        external = domain.get('display', False)
        
    #process url prefix with '/'
    if filename.startswith('/'):
        if filename.endswith('/'):
            filename = filename[:-1]
        if kwargs:
            filename += '?' + urllib.urlencode(kwargs)
        if external:
            return urljoin(domain.get('domain', ''), filename)
        return filename
    
    #process url has already domain info
    r = urlparse(filename)
    if r.scheme or r.netloc:
        x = list(r)
        if kwargs:
            x[4] = urllib.urlencode(kwargs)
            return urlunparse(x)
        else:
            return filename
    
    kwargs['filename'] = filename
    url_adapter = get_url_adapter('static')
    return url_adapter.build('uliweb.contrib.staticfiles.static',
        kwargs, force_external=external)

def static(filename):
    pass

