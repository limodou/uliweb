from uliweb.utils.common import log
from uliweb.core import dispatch
from uliweb.orm import get_model

class CreatingUserError(Exception):pass

def _get_auth_key(request):
    return request.settings.AUTH.AUTH_KEY

def get_user(request):
    """
    return user
    """
    session_key = _get_auth_key(request)
    user_id = request.session.get(session_key)
    if user_id:
        User = get_model('user')
        return User.get(user_id)

def create_user(request, username, password):
    """
    return flag, result(result can be an User object or just True, {} for errors)
    """
    
    try:
        User = get_model('user')
        user = User.get(User.c.username==username)
        if user:
            return False, {'username':"Username is already existed!"}
        user = User(username=username, password=password)
        user.set_password(password)
        user.save()
        return True, user
    except Exception, e:
        log.exception(e)
        return False, {'_': "Creating user failed!"}
    
def change_password(request, username, password):
    User = get_model('user')
    user = User.get(User.c.username==username)
    user.set_password(password)
    user.save()
    return True

def delete_user(request, username):
    if result:
        User = get_model('user')
        user = User.get(User.c.username==username)
        if user:
            user.delete()
    return result
    
def authenticate(request, username, password):
    User = get_model('user')
    user = User.get(User.c.username==username)
    if user:
        if user.check_password(password):
            return True, user
        else:
            return False, {'password': "Password isn't correct!"}
    else:
        return False, {'username': 'Username is not existed!'}

def login(request, username):
    """
    return user
    """
    import datetime
    User = get_model('user')
    
    user = User.get(User.c.username==username)
    user.last_login = datetime.datetime.now()
    user.save()
    request.session[_get_auth_key(request)] = user.id
    if hasattr(request, 'user'):
        request.user = user
    return True
    
def logout(request):
    """
    Remove the authenticated user's ID from the request.
    """
    request.session.delete()
    request.user = None
    return True

def require_login(f, login_url='/login'):
    from uliweb.utils.common import wraps
    
    @wraps(f)
    def _f(*args, **kwargs):
        r = if_login(login_url)
        if r:
            return r
        return f(*args, **kwargs)
    return _f

def if_login(login_url='/login'):
    from uliweb import request, redirect
    import urllib
    
    if not request.user:
        if request.query_string:
            path = urllib.quote(request.path+'?'+request.query_string)
        else:
            path = request.path
        return redirect(login_url + '?next=%s' % path)
    