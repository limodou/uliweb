import copy
from uliweb.core.SimpleFrame import url_for
from uliweb.core.dispatch import bind, call
from StringIO import StringIO

__weight = 0

def bind_menu(caption, id=None, parent_menu_id=None, weight=None):
    
    def decorate(f, id=id, caption=caption, parent_menu_id=parent_menu_id, weight=weight):
        global __weight
        
        if not id:
            id = caption
            
        if not weight:
            __weight += 10
            weight = __weight
        else:
            __weight = max(__weight, weight)
            
        if callable(f):
            f_name = f.__name__
            endpoint = f.__module__ + '.' + f.__name__
        else:
            f_name = f.split('.')[-1]
            endpoint = f
        
        def _f(sender, menus):
            menus.append((parent_menu_id, (weight, id, caption, endpoint)))
        bind('add_menu')(_f)
        return f
    
    return decorate

def mergemenu(menulist):
    m = {}

    for pid, menu in menulist:
        if not isinstance(menu, list):
            menu = [menu]
        newmenu = copy.deepcopy(menu)
        if m.has_key(pid):
            m[pid].extend(newmenu)
        else:
            m[pid] = newmenu
        m[pid].sort()
    return m

def menu(current='settings'):
    out = StringIO()
    menus = []
    call(None, 'add_menu', menus)
    
    mlist = mergemenu(menus)
    out.write('<ul>')
    for m in mlist[None]:
        weight, id, caption, endpoint = m
        if id == current:
            out.write('<li class="active"><strong>%s</strong></li>' % caption)
        else:
            out.write('<li><a href="%s">%s</a></li>' % (url_for(endpoint), caption))
        
        submenu(mlist, id)
    out.write('</ul>')
    return out.getvalue()

def submenu(mlist, idname):
    pass
