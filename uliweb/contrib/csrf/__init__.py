import time
import uuid
from werkzeug.exceptions import Forbidden

def csrf_token():
    """
    Get csrf token or create new one
    """
    from uliweb import request, settings
    from uliweb.utils.common import safe_str
    
    v = {}
    token_name = settings.CSRF.cookie_token_name
    if not request.session.deleted and request.session.get(token_name):
        v = request.session[token_name]
        if time.time() >= v['created_time'] + v['expiry_time']:
            v = {}
        else:
            v['created_time'] = time.time()
    if not v:
        token = request.cookies.get(token_name)
        if not token:
            token = uuid.uuid4().get_hex()
        
        v = {'token':token, 'expiry_time':settings.CSRF.timeout, 'created_time':time.time()}

    if not request.session.deleted:
        request.session[token_name] = v
    return safe_str(v['token'])

def check_csrf_token():
    """
    Check token
    """
    from uliweb import request, settings

    token = (request.params.get(settings.CSRF.form_token_name, None) or
             request.headers.get("X-Xsrftoken") or
             request.headers.get("X-Csrftoken"))

    if not token:
        raise Forbidden("CSRF token missing.")
    if csrf_token() != token:
        raise Forbidden("CSRF token dismatched.")
