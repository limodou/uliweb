from uliweb.orm import get_model
from uliweb.utils.common import import_attr

__all__ = ['add_role_func', 'register_role_method',
    'superuser', 'trusted', 'anonymous', 'has_role', 'has_permission']

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
    
def has_role(user, role, **kwargs):
    """
    Judge is the user belongs to the role, and if does, then return the role object
    if not then return False. kwargs will be passed to role_func.
    """
    Role = get_model('role')
    if isinstance(user, (unicode, str)):
        User = get_model('user')
        user = User.get(User.c.username==user)
        
    if isinstance(role, (str, unicode)):
        role = Role.get(Role.c.name==role)
        if not role:
            return False
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
    return False

def has_permission(user, permission, **role_kwargs):
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
        
    perm = Perm.get(Perm.c.name==permission)
    if not perm:
        return False
    
    for role in perm.perm_roles.with_relation().all():
        flag = has_role(user, role, **role_kwargs)
        if flag:
            return flag
    return False

