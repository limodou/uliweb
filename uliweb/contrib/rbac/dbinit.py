import uliweb
from uliweb.utils.common import safe_str
from uliweb.orm import get_model, set_dispatch_send

set_dispatch_send(False)

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
        msg = 'Add Role(%s)...' % name
    else:
        role.update(description=description, reserve=reserve)
        msg = 'Update Role(%s)...' % name
    flag = role.save()
    if flag:
        print msg

def process_permission_roles(perm, v):
    """
    v is roles
    """
    if isinstance(v, (tuple, list)):
        roles = v
    else:
        roles = [v]
    for r in roles:
        if isinstance(r, (tuple, list)):
            role_name, role_props = r
        else:
            role_name, role_props = r, ''
        role = Role.get(Role.c.name == role_name)
        if not role:
            raise Exception, 'Role [%s] not found.' % r
        rel = Rel.get((Rel.c.role==role.id) & (Rel.c.permission==perm.id))
        if not rel:
            rel = Rel(role=role, permission=perm, props=role_props)
            msg = 'Add Relation(Permision=%s, Role=%s)...' % (name, role_name)
        else:
            rel.update(props=role_props)
            msg = 'Update Relation(Permision=%s, Role=%s)...' % (name, role_name)
            
        flag = rel.save()
        if flag:
            print msg
    
p = uliweb.settings.get('PERMISSIONS', {})
for name, v in p.items():
    if isinstance(v, (tuple, list)):
        if len(v) == 2:
            description, props = v
            roles = []
        else:
            description, roles, props = v
    elif isinstance(v, dict):
        description = v.get('description', '')
        props = v.get('props', '')
        roles = v.get('roles', [])
    else:
        description, roles, props = v, [], ''
    perm = Perm.get(Perm.c.name==name)
    if not perm:
        perm = Perm(name=name, description=description, props=props)
        msg = 'Add Permission(%s)...' % name
    else:
        perm.update(description=description, props=props)
        msg = 'Update Permission(%s)...' % name
    flag = perm.save()
    if flag:
        print msg
    process_permission_roles(perm, roles)
    
p = uliweb.settings.get('ROLES_PERMISSIONS', {})
for name, v in p.items():
    perm = Perm.get(Perm.c.name==name)
    if not perm:
        raise Exception, 'Permission [%s] not found.' % name
        
    process_permission_roles(perm, v)

