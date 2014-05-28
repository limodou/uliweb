from rbac import *

def prepare_default_env(sender, env):
    from uliweb import functions

    env['has_permission'] = functions.has_permission
    env['has_role'] = functions.has_role

def after_init_apps(sender):
    from uliweb import settings
    from rbac import register_role_method
    
    if 'ROLES' in settings:
        for k, v in settings.get_var('ROLES', {}).iteritems():
            if isinstance(v, (list, tuple)) and len(v) > 1:
                method = v[1]
                if method:
                    register_role_method(k, method)

def startup_installed(sender):
    from uliweb.core import template
    from .tags import PermissionNode, RoleNode
    
    template.register_node('permission', PermissionNode)
    template.register_node('role', RoleNode)
