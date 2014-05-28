from uliweb.orm import get_model
from uliweb.utils.common import import_attr, wraps
from uliweb.i18n import ugettext_lazy as _

__all__ = ['add_role_func', 'register_role_method',
    'superuser', 'trusted', 'anonymous', 'has_role', 'has_permission',
    'check_role', 'check_permission']

def call_func(func, kwargs):
    import inspect
    
    args = {}
    for x in inspect.getargspec(func).args:
        try:
            args[x] = kwargs[x]
        except KeyError:
            raise Exception, "Missing args %s" % x
    return func(**args)

def superuser(user):
    return user and user.is_superuser

def trusted(user):
    return user is not None

def anonymous(user):
    return not user

__role_funcs__ = {}

def register_role_method(role_name, method):
    __role_funcs__[role_name] = method

def add_role_func(name, func):
    """
    Role_func should have 'user' parameter
    """
    global __role_funcs__
    
    __role_funcs__[name] = func
    
def has_role(user, *roles, **kwargs):
    """
    Judge is the user belongs to the role, and if does, then return the role object
    if not then return False. kwargs will be passed to role_func.
    """
    Role = get_model('role')
    if isinstance(user, (unicode, str)):
        User = get_model('user')
        user = User.get(User.c.username==user)
        
    for role in roles:
        if isinstance(role, (str, unicode)):
            role = Role.get(Role.c.name==role)
            if not role:
                continue
        name = role.name
        
        func = __role_funcs__.get(name, None)
        if func:
            if isinstance(func, (unicode, str)):
                func = import_attr(func)
                
            assert callable(func)
            
            para = kwargs.copy()
            para['user'] = user
            flag = call_func(func, para)
            if flag:
                return role
        flag = role.users.has(user)
        if flag:
            return role
        
        flag = role.usergroups_has_user(user)
        if flag:
            return role
    return False

def has_permission(user, *permissions, **role_kwargs):
    """
    Judge if an user has permission, and if it does return role object, and if it doesn't
    return False. role_kwargs will be passed to role functions.
    With role object, you can use role.relation to get Role_Perm_Rel object.
    """
    Role = get_model('role')
    Perm = get_model('permission')
    if isinstance(user, (unicode, str)):
        User = get_model('user')
        user = User.get(User.c.username==user)
        
    for name in permissions:
        perm = Perm.get(Perm.c.name==name)
        if not perm:
            continue
        
        flag = has_role(user, *list(perm.perm_roles.with_relation().all()), **role_kwargs)
        if flag:
            return flag
        
    return False

def check_role(*roles, **args_map):
    """
    It's just like has_role, but it's a decorator. And it'll check request.user
    """
    def f1(func, roles=roles):
        @wraps(func)
        def f2(*args, **kwargs):
            from uliweb import request, error
            
            arguments = {}
            for k, v in args_map.items():
                if v in kwargs:
                    arguments[k] = kwargs[v]
            if not has_role(request.user, *roles, **arguments):
                error(_("You have no roles to visit this page."))
            return func(*args, **kwargs)
        return f2
    return f1

def check_permission(*permissions, **args_map):
    """
    It's just like has_role, but it's a decorator. And it'll check request.user
    """
    def f1(func, permissions=permissions):
        @wraps(func)
        def f2(*args, **kwargs):
            from uliweb import request, error

            arguments = {}
            for k, v in args_map.items():
                if v in kwargs:
                    arguments[k] = kwargs[v]
            if not has_permission(request.user, *permissions, **arguments):
                error(_("You have no permissions to visit this page."))
            return func(*args, **kwargs)
        return f2
    return f1
