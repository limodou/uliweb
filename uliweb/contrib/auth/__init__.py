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
        algo, salt, hsh = l
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

def get_auth_user():
    """
    Find auth user
    :return: user object could be a model instance or a dict
    """
    from uliweb import request
    from uliweb import settings

    user_fieldname = settings.get_var('AUTH/GET_AUTH_USER_FIELDNAME', 'id')

    session_key = _get_auth_key()
    user_id = request.session.get(session_key)
    if user_id:
        if isinstance(user_id, dict):
            return user_id
        else:
            User = get_model('user')
            user = User.get(User.c[user_fieldname]==user_id)
            return user


def get_user_session_key(user_id):
    return '__USER_SESSION:{}'.format(user_id)


def set_user_session(user):
    """
    Set user session
    :param user: user object chould be model instance or dict
    :return:
    """
    from uliweb import settings, request

    user_fieldname = settings.get_var('AUTH/GET_AUTH_USER_FIELDNAME', 'id')
    share_session = settings.get_var('AUTH/AUTH_SHARE_USER_SESSION', False)
    if isinstance(user, dict):
        user_id = user[user_fieldname]
    else:
        user_id = getattr(user, user_fieldname)

    if share_session:
        cache = functions.get_cache()
        key = get_user_session_key(user_id)
        session_id = cache.get(key, None)
        log.debug('Auth: user session user_id={}, session_id={}, key={}'.format(user_id, session_id, key))
        if not session_id:
            request.session.save()
            log.debug('Auth: set user session mapping userid={}, '
                      'session_id={}, expiry time={}'.format(user_id,
                                                             request.session.key,
                                                             request.session.expiry_time))
            cache.set(key, request.session.key, expire=request.session.expiry_time)
        elif session_id != request.session.key:
            log.debug('Auth: load oldkey={}, key={}'.format(request.session.key, session_id))
            request.session.delete()
            request.session.load(session_id)
    if isinstance(user, dict):
        request.session[_get_auth_key()] = user
    else:
        request.session[_get_auth_key()] = user_id
    request.user = user


def update_user_session_expiry_time():
    from uliweb import settings, request

    user_fieldname = settings.get_var('AUTH/GET_AUTH_USER_FIELDNAME', 'id')
    share_session = settings.get_var('AUTH/AUTH_SHARE_USER_SESSION', False)
    user = request.user
    if user and share_session:
        if isinstance(user, dict):
            user_id = user[user_fieldname]
        else:
            user_id = getattr(user, user_fieldname)
        cache = functions.get_cache()
        key = get_user_session_key(user_id)
        log.debug('Auth: update user session expiry time, userid={}, session_id={}, '
                  'expiry_time={}'.format(key, request.session.key,
                                          request.session.expiry_time))
        cache.set(key, request.session.key, expire=request.session.expiry_time)


def delete_user_session():
    from uliweb import settings, request

    user_fieldname = settings.get_var('AUTH/GET_AUTH_USER_FIELDNAME', 'id')
    share_session = settings.get_var('AUTH/AUTH_SHARE_USER_SESSION', False)
    user = request.user
    if user and share_session:
        if isinstance(user, dict):
            user_id = user[user_fieldname]
        else:
            user_id = getattr(user, user_fieldname)
        cache = functions.get_cache()
        key = get_user_session_key(user_id)
        log.debug('Auth: delete user session, userid={}, session_id={}'.format(
            key, request.session.key))
        cache.delete(key)


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
        return False, {'username': _('"{}" is not existed!').format(username)}

def authenticate(username, password, auth_type=None):
    from uliweb import settings

    auth_type = auth_type or settings.AUTH.AUTH_DEFAULT_TYPE

    errors = {}
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
                    errors = d
        else:
            log.error("auth_type %s not in config"%(t))

    return False, errors

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
    set_user_session(user)
    return True


def logout():
    """
    Remove the authenticated user's ID from the request.
    """
    from uliweb import request

    delete_user_session()
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
