from uliweb.orm import get_model
import logging
from uliweb.i18n import ugettext_lazy as _
from uliweb import functions
from uliweb.utils.common import import_attr

log = logging.getLogger(__name__)

def get_hexdigest(algorithm, salt, raw_password):
    """
    Returns a string of the hexdigest of the given plaintext password and salt
    using the given algorithm ('md5', 'sha1' or 'crypt').
    """
    if isinstance(salt, unicode):
        salt = salt.encode('utf8')
    if algorithm == 'crypt':
        try:
            import crypt
        except ImportError:
            raise ValueError('"crypt" password algorithm not supported in this environment')
        return crypt.crypt(raw_password, salt)
    # The rest of the supported algorithms are supported by hashlib, but
    # hashlib is only available in Python 2.5.
    try:
        import hashlib
    except ImportError:
        if algorithm == 'md5':
            import md5
            return md5.new(salt + raw_password).hexdigest()
        elif algorithm == 'sha1':
            import sha
            return sha.new(salt + raw_password).hexdigest()
    else:
        if algorithm == 'md5':
            return hashlib.md5(salt + raw_password).hexdigest()
        elif algorithm == 'sha1':
            return hashlib.sha1(salt + raw_password).hexdigest()
    raise ValueError("Got unknown password algorithm type in password.")

def check_password(raw_password, enc_password):
    """
    Returns a boolean of whether the raw_password was correct. Handles
    encryption formats behind the scenes.
    """
    l = enc_password.split('$')
    #only password of built-in user can split to 3
    if len(l)==3:
        algo, salt, hsh = l.split('$')
        return hsh == get_hexdigest(algo, salt, raw_password)
    else:
        return False

def encrypt_password(raw_password):
    import random
    algo = 'sha1'
    salt = get_hexdigest(algo, str(random.random()), str(random.random()))[:5]
    hsh = get_hexdigest(algo, salt, raw_password)
    return '%s$%s$%s' % (algo, salt, hsh)

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

def default_authenticate(username, password):
    User = get_model('user')
    if isinstance(username, (str, unicode)):
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

def authenticate(username, password, auth_type=None):
    from uliweb import settings

    auth_type = auth_type or settings.AUTH.AUTH_DEFAULT_TYPE

    err_msg = ''
    if not isinstance(auth_type, (list, tuple)):
        auth_type = [auth_type]

    for t in auth_type:
        if t in settings.AUTH_CONFIG:
            func_path = settings.AUTH_CONFIG[t].get('authenticate')
            if func_path:
                func = import_attr(func_path)
                f, d = func(username, password)
                if f:
                    log.info("login successfully, auth_type: %s"%(t))
                    return f, d
                else:
                    log.error("fail to login, auth_type: %s, err: %s"%(t,d))
                    err_msg = d
        else:
            log.error("auth_type %s not in config"%(t))

    return False, {'username':err_msg}

def login(username):
    """
    return user
    """
    from uliweb.utils.date import now
    from uliweb import request

    User = get_model('user')

    if isinstance(username, (str, unicode)):
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
