from .rbac import *
import six

def prepare_default_env(sender, env):
    from .rbac import has_permission, has_role
    env['has_permission'] = has_permission
    env['has_role'] = has_role
    
def after_init_apps(sender):
    from uliweb import settings
    from .rbac import register_role_method
    
    if 'ROLES' in settings:
        for k, v in six.iteritems(settings.get_var('ROLES', {})):
            if isinstance(v, (list, tuple)) and len(v) > 1:
                method = v[1]
                if method:
                    register_role_method(k, method)

def startup_installed(sender):
    from uliweb.core import template
    from .tags import PermissionNode, RoleNode
    
    template.register_node('permission', PermissionNode)
    template.register_node('role', RoleNode)
