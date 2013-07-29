from uliweb.orm import get_model
import logging
from uliweb.i18n import ugettext_lazy as _
from uliweb import functions
import six

log = logging.getLogger('uliweb.app')

def _get_auth_key():
    from uliweb import settings
    
    return settings.AUTH.AUTH_KEY

def get_user():
    """
    return user
    """
    from uliweb import request
    
    session_key = _get_auth_key()
    user_id = request.session.get(session_key)
    if user_id:
        User = get_model('user')
        return User.get(user_id)

def create_user(username, password, **kwargs):
    """
    return flag, result(result can be an User object or just True, {} for errors)
    """
    try:
        User = get_model('user')
        user = User.get(User.c.username==username)
        if user:
            return False, {'username':"Username is already existed!"}
        user = User(username=username, password=password, **kwargs)
        user.set_password(password)
        user.save()
        return True, user
    except Exception as e:
        log.exception(e)
        return False, {'_': "Creating user failed!"}
    
def authenticate(username, password):
    User = get_model('user')
    if isinstance(username, six.string_types):
        user = User.get(User.c.username==username)
    else:
        user = username
    if user:
        if user.check_password(password):
            return True, user
        else:
            return False, {'password': _("Password isn't correct!")}
    else:
        return False, {'username': _('Username is not existed!')}

def login(username):
    """
    return user
    """
    from uliweb.utils.date import now
    from uliweb import request 
    
    User = get_model('user')
    
    if isinstance(username, six.string_types):
        user = User.get(User.c.username==username)
    else:
        user = username
    user.last_login = now()
    user.save()
    request.session[_get_auth_key()] = user.id
    request.user = user
    return True
    
def logout():
    """
    Remove the authenticated user's ID from the request.
    """
    from uliweb import request
    
    request.session.delete()
    request.user = None
    return True

def require_login(f=None, next=None):
    from uliweb.utils.common import wraps
    
    def _login(next=None):
        from uliweb import request, Redirect, url_for
        
        if not request.user:
            path = functions.request_url()
            Redirect(next or url_for('login', next=path))
    
    if not f:
        _login(next=next)
        return
    
    @wraps(f)
    def _f(*args, **kwargs):
        _login(next=next)
        return f(*args, **kwargs)
    return _f

    