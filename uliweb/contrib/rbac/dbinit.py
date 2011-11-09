import uliweb
from uliweb.utils.common import safe_str
from uliweb.orm import get_model

Role = get_model('role')
Perm = get_model('permission')
Rel = get_model('role_perm_rel')

r = uliweb.settings.get('ROLES', {})
for name, v in r.items():
    if isinstance(v, (tuple, list)):
        if len(v) == 2:
            description, method = v
            reserve = False
        else:
            description, method, reserve = v
    else:
        description, reserve = v, True
    role = Role.get(Role.c.name==name)
    if not role:
        role = Role(name=safe_str(name), description=safe_str(description), reserve=reserve)
    else:
        role.update(description=description, reserve=reserve)
    role.save()

p = uliweb.settings.get('PERMISSIONS', {})
for name, v in p.items():
    if isinstance(v, tuple):
        description, props = v
    else:
        description, props = v, None
    perm = Perm.get(Perm.c.name==name)
    if not perm:
        perm = Perm(name=name, description=description, props=props)
    else:
        perm.update(description=description, props=props)
    perm.save()
    
p = uliweb.settings.get('ROLES_PERMISSIONS', {})
for name, v in p.items():
    perm = Perm.get(Perm.c.name==name)
    if not perm:
        raise Exception, 'Permission [%s] not found.' % name
        
    if isinstance(v, tuple):
        roles = v
    else:
        roles = [v]
    for r in roles:
        if isinstance(r, (tuple, list)):
            role_name, role_props = r
        else:
            role_name, role_props = r, None
        role = Role.get(Role.c.name == role_name)
        if not role:
            raise Exception, 'Role [%s] not found.' % r
        rel = Rel(role=role, permission=perm, props=role_props)
        rel.save()

