#coding=utf-8
from uliweb.core.SimpleFrame import expose
from uliweb.contrib.develop.menu import bind_menu
from uliweb.utils.common import log
from uliweb.utils.common import pkg, is_pyfile_exist

@expose('/develop')
@bind_menu('Settings', weight=10)
def develop_index():
    return {}

@expose('/develop/appsinfo')
@bind_menu('Apps Info', weight=20)
def develop_appsinfo():
    return {'apps':application.apps}

@expose('/develop/urls')
@bind_menu('Urls', weight=30)
def develop_urls():
    u = []
    for r in application.url_map.iter_rules():
        if r.methods:
            methods = ' '.join(list(r.methods))
        else:
            methods = ''
        u.append((r.rule, methods, r.endpoint))
    u.sort()
    
    return {'urls':u}

@expose("/develop/global")
@bind_menu('View Global', weight=40)
def develop_globals():
#    glob = globals()
#    glo = [ (key,glob[key]) for key in glob.keys() if callable(glob[key]) ]
#    un = [(key, str(glob[key]) or "none") for key in glob.keys() if not callable(glob[key]) ]
#    glo.extend(un)
#    glob = sorted(glob)
    
    return {"glo":env}
 
from uliweb.utils.pyini import Ini
import os

@expose("/develop/build")
@bind_menu('Build')
def develop_build():
    from uliweb.utils.common import pkg
    
    import uliweb.core.SimpleFrame as sf
    app_apps = sf.get_apps(application.apps_dir)
    
    contrib_path = pkg.resource_filename('uliweb.contrib', '')
    apps_dirs = [(application.apps_dir, ''), (contrib_path, 'uliweb.contrib')]
    
    #using entry point to find installed apps
    try:
        from pkg_resources import iter_entry_points
    except:
        iter_entry_points = None
    if iter_entry_points:
        #process apps group
        for p in iter_entry_points('uliweb_apps'):
            apps_dirs.append((os.path.join(p.dist.location, p.module_name), p.module_name))
            
    catalogs, apps = get_apps(application, apps_dirs, app_apps)
    
    if iter_entry_points:
        #proces single app
        for p in iter_entry_points('uliweb_app'):
            _get_app(os.path.join(p.dist.location, p.module_name), p.module_name, apps, catalogs, app_apps)
    
    from forms import GenericForm
    
    f = GenericForm(method="post")
    
    if request.method == 'GET':
#        ini = Ini(os.path.join(application.apps_dir, 'settings.ini'))
        ini_to_form(f, application.settings)
        
    else:
        r = f.validate(request.params)
        if r:
            ini = Ini(os.path.join(application.apps_dir, 'settings.ini'))
            flag = form_to_ini(f, ini, application.settings)
            if flag:
                ini.save()
        
    return {'catalogs':catalogs, 'generic_form':f}

@expose('/develop/app_edit')
def develop_edit_app():
    ini = Ini(os.path.join(application.apps_dir, 'settings.ini'))
    flag = False
    module = str(request.GET['module'])
    
    import uliweb.core.SimpleFrame as sf
    app_apps = sf.get_apps(application.apps_dir)
    
    if request.GET['action'] == 'add':
        if not ini.GLOBAL.get('INSTALLED_APPS'):
            ini.GLOBAL.INSTALLED_APPS = app_apps
        if module not in ini.GLOBAL.INSTALLED_APPS:
            ini.GLOBAL.INSTALLED_APPS.append(module)
            flag = True
    else:
        if not ini.GLOBAL.get('INSTALLED_APPS'):
            ini.GLOBAL.INSTALLED_APPS = app_apps
        if module in ini.GLOBAL.INSTALLED_APPS:
            ini.GLOBAL.INSTALLED_APPS.remove(module)
            flag = True
    
    if flag:
        ini.save()
    return 'ok'
    
def ini_to_form(form, ini):
    for k, obj in form.fields.items():
        if 'key' in obj.kwargs:
            key = obj.kwargs['key']
            v = ini.get_var(key)
            if v:
                getattr(form, k).data = v

def form_to_ini(form, ini, default=None):
    flag = False
    for k, obj in form.fields.items():
        if 'key' in obj.kwargs:
            key = obj.kwargs['key']
            v = ini.get_var(key)
            if default:
                d = default.get_var(key)
            else:
                d = None
            value = getattr(form, k).data
            if default:
                if value == d:
                    flag = ini.del_var(key) or flag
                    continue
            if value != v:
                flag = ini.set_var(key, value) or flag
    
    return flag
    
def _get_app(app_path, modname, apps, catalogs, app_apps, parent_module=''):
    info_ini = os.path.join(app_path, 'info.ini')
    if os.path.exists(info_ini):
        info = get_app_info(modname, app_path, info_ini)
        if parent_module:
            info['module'] = parent_module + '.' + modname
        else:
            info['module'] = modname
        if info['module'] in app_apps:
            info['selected'] = True
        else:
            info['selected'] = False
            
        apps[modname] = info
        d = catalogs.setdefault(info['catalog'], [])
        d.append(info)
   
def _get_apps(application, path, parent_module, catalogs, apps, app_apps):
    if not os.path.exists(path):
        return
    for p in os.listdir(path):
        if p in ['.svn', 'CVS'] or p.startswith('.') or p.startswith('_'):
            continue
        app_path = os.path.join(path, p)
        
        if not os.path.isdir(app_path):
            continue
        
        _get_app(app_path, p, apps, catalogs, app_apps, parent_module)
               
        _path = os.path.join(path, p)
        if is_pyfile_exist(_path, '__init__'):
            if parent_module:
                m = parent_module + '.' + p
            else:
                m = p
            _get_apps(application, _path, m, catalogs, apps, app_apps)

def get_apps(application, apps_dirs, app_apps):
    catalogs = {}
    apps = {}
    
    for path, parent_module in apps_dirs:
        _get_apps(application, path, parent_module, catalogs, apps, app_apps)
        
    return catalogs, apps

@expose('/develop/app_conf')
def develop_app_conf():
    module = request.GET['module']
    app_path = pkg.resource_filename(module, '')
    
    form = '<h3>Nothing need to configure!</h3>'
    message = ''
    if is_pyfile_exist(app_path, 'conf'):
        try:
            mod = __import__(module + '.conf', {}, {}, [''])
            f = getattr(mod, 'ManageForm', None)
            if f:
                form = f(action=url_for(develop_app_conf)+'?module=%s' % module, method='post')
                if request.method == 'POST':
                    ini = Ini(os.path.join(application.apps_dir, 'settings.ini'))
                    default_ini = Ini(os.path.join(app_path, 'settings.ini'))
                    r = form.validate(request.POST)
                    if r:
                        flag = form_to_ini(form, ini, default_ini)
                        if flag:
                            message = '<div class="note">Changes have been saved!</div>'
                            ini.save()
                        else:
                            message = '<div class="important">There are no changes.</div>'
                    else:
                        message = '<div class="warning">There are some errors.</div>'
                elif request.method == 'GET':
                    ini = Ini()
                    ini_file = os.path.join(app_path, 'settings.ini')
                    if os.path.exists(ini_file):
                        ini.read(ini_file)
                    ini.read(os.path.join(application.apps_dir, 'settings.ini'))
                    ini_to_form(form, ini)
        
        except ImportError, e:
            log.exception(e)
    
    return message + str(form)
                
def get_app_info(name, app_path, info_ini):
    catalog = 'No Catalog'
    desc = ''
    title = name.capitalize()
    icon = 'app_icon.png'
    author = ''
    version = ''
    homepage = ''
    
    if os.path.exists(info_ini):
        ini = Ini(info_ini)
        catalog = ini.info.get('catalog', catalog) or catalog
        desc = ini.info.get('description', desc) or desc
        title = ini.info.get('title', title) or title
        icon = ini.info.get('icon', icon) or icon
        icon_file = os.path.join(app_path, 'static', icon)
        author = ini.info.get('author', author) or author
        version = ini.info.get('version', version) or version
        homepage = ini.info.get('homepage', homepage) or homepage
        
    return {'catalog':catalog, 'desc':desc, 'title':title, 'name':name, 
            'path':app_path, 'icon':icon, 'author':author, 
            'version':version, 'homepage':homepage} 