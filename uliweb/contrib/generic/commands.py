import os
from optparse import make_option
from uliweb.core.commands import Command, get_input, get_answer
from uliweb.core.template import template_file

def camel_to_cap(s):
    import re
    
    return re.sub('^\w|_\w', lambda x:x.group()[-1].upper(), s)
    
class GenericCommand(Command):
    name = 'generic'
    option_list = (
        make_option('-r', dest='replace', action='store_true', help='Replace existed views file.'),
        make_option('-a', '--appname', dest='appname', help='App name.'),
        make_option('-t', '--tablename', dest='tablename', help='Table name.'),
        make_option('-c', '--classname', dest='classname', help='Class name.'),
        make_option('-d', '--download', dest='download', action='store_true', help='Download support.'),
        make_option('--downloadfile', dest='downloadfile', help='Download filename.'),
        make_option('--viewfile', dest='viewfile', help='View file name.'),
        make_option('--layout', dest='layout', help='Layout template name.'),
        make_option('-u', '--url', dest='url', help='Class View URL prefix.'),
        make_option('-p', '--pagination', action='store_true', dest='pagination', help='Enable pagination.'),
        make_option('-q', '--query', action='store_true', dest='query', help='Enable query.'),
        make_option('--addview_popup', dest='addview_popup', action='store_true', help='Add View using popup or using new window.'),
        make_option('--addview_ajax', dest='addview_ajax', action='store_true', help='Add View using ajax or not.'),
        make_option('--editview_popup', dest='editview_popup', action='store_true', help='Edit View using popup or using new window.'),
        make_option('--editview_ajax', dest='editview_ajax', action='store_true', help='Edit View using ajax or not.'),
        make_option('--deleteview_ajax', dest='deleteview_ajax', action='store_true', help='Delete View using ajax or not.'),
        make_option('--theme', dest='theme', help='theme name, available themes is [angularjs, html, easyui, avalon, mmgrid].'),
    )
    help = 'Create a scaffold for an generic(CRUD) admin interface.'
    args = ''
    check_apps_dirs = False
    check_apps = False
    
    def handle(self, options, global_options, *args):
        d = {}
        d['appname'] = get_input("Appname:", option_value=options.appname).lower()
        d['tablename'] = get_input("Table Name:", option_value=options.tablename).lower()
        d['theme'] = get_input("Creation Theme([a]ngularjs, [h]tml), [e]sayui)[a], [m]mGrid, a[v]alon:", default="m", choices='ahemv', option_value=options.theme)
        view_name = camel_to_cap(d['tablename'])+'View'
        view_file_name = 'views_%s.py' % d['tablename']
        url_prefix = '/'+d['appname']
        d['classname'] = get_input("View Class Name [%s]:" % view_name, default=view_name, option_value=options.classname)
        d['viewfile'] = get_input("Save views to [%s]:" % view_file_name, default=view_file_name, option_value=options.viewfile)
        layout_name = d['appname'].lower() + '_layout.html'
        d['layout'] = get_input("Layout template name [%s]:" % layout_name, default=layout_name, option_value=options.layout)
        d['url'] = get_input("Class View URL prefix [%s]:" % url_prefix, default=url_prefix, option_value=options.url)
        d['pagination'] = get_answer("Enable pagination", quit='q') == 'Y'
        d['query'] = get_answer("Enable query", quit='q') == 'Y'
        d['download'] = get_answer("Enable download", quit='q') == 'Y'
        if d['download']:
            d['downloadfile'] = get_input("Download filename [%s]:" % 'download.xls', default='download.xls', option_value=options.downloadfile)
        d['addview_popup'] = get_answer("Add View using popup", quit='q') == 'Y'
        d['addview_ajax'] = get_answer("Add View using ajax", quit='q') == 'Y'
        d['editview_popup'] = get_answer("Edit View using popup", quit='q') == 'Y'
        d['editview_ajax'] = get_answer("Edit View using ajax", quit='q') == 'Y'
        d['deleteview_ajax'] = get_answer("Delete View using ajax", quit='q') == 'Y'
        
        theme = {'a':'angularjs', 'h':'html', 'e':'easyui', 'm':'mmgrid', 'v':'avalon'}
        
        d['theme_name'] = theme_name = theme.get(d['theme'])
        self.process(theme_name, d, options, global_options, args)
        
    def copy_view(self, viewfile_template, data, viewfile_dst, replace):
        text = template_file(viewfile_template, data).replace('\r\n', '\n')
        if replace or not os.path.exists(viewfile_dst):
            text = '#coding=utf8\n' + text
            f = open(viewfile_dst, 'w')
        else:
            if os.path.getsize(viewfile_dst) == 0:
                text = '#coding=utf8\n' + text
            f = open(viewfile_dst, 'a')
        f.write(text)
        f.close()
        
    def copy_template(self, src_template, data, dst_template):
        text = template_file(src_template, data).replace('\r\n', '\n')
        f = open(dst_template, 'w')
        f.write(text)
        f.close()
        
    def process(self, theme_name, data, options, global_options, args):
        from uliweb.utils.common import pkg, copy_dir
        import shutil
        from uliweb.utils.pyini import Ini
        
        #if there is no apps/appname then create files in current directory
        
        path = os.path.join(global_options.apps_dir, data['appname'])
        if not os.path.exists(path):
            path = '.'
            
        gpath = pkg.resource_filename('uliweb.contrib.generic', 'template_files/%s' % theme_name)
        
        def render(fpath, dst, df):
            text = template_file(fpath, data).replace('\r\n', '\n')
            open(df, 'w').write(text)
            return True
        
        #copy template files
        copy_dir(os.path.join(gpath, 'templates'), os.path.join(path, 'templates', data['classname']),
            processor=render)

        #process config.ini
        src_config = os.path.join(gpath, 'config.ini')
        dst_config = os.path.join(path, 'config.ini')
        if os.path.exists(dst_config):
            dst = Ini(dst_config)
            src = Ini(src_config)
            for x in src.DEPENDS.REQUIRED_APPS:
                if x not in dst.DEPENDS.REQUIRED_APPS:
                    dst.DEPENDS.REQUIRED_APPS.append(x)
            dst.save()
        else:
            shutil.copy2(os.path.join(gpath, 'config.ini'), path)
            
        cpath = pkg.resource_filename('uliweb.contrib.generic', 'template_files/common')

        #check if layout is existed, if not then create it
        layout_file = os.path.join(path, 'templates', data['layout'])
        if not os.path.exists(layout_file):
            self.copy_template(os.path.join(cpath, 'layout.html'), data, layout_file)

        #copy views file
        self.copy_view(os.path.join(cpath, 'views.py.tmpl'), data, 
            os.path.join(path, data['viewfile']), options.replace)
        
        #copy add, edit, view
        dpath = os.path.join(path, 'templates', data['classname'])
        if data['addview_popup']:
            self.copy_template(os.path.join(cpath, 'ajax_add.html'), data, os.path.join(dpath, 'add.html'))
        else:
            self.copy_template(os.path.join(cpath, 'add.html'), data, os.path.join(dpath, 'add.html')) 
        if data['editview_popup']:
            self.copy_template(os.path.join(cpath, 'ajax_edit.html'), data, os.path.join(dpath, 'edit.html')) 
        else:
            self.copy_template(os.path.join(cpath, 'edit.html'), data, os.path.join(dpath, 'edit.html')) 
        self.copy_template(os.path.join(cpath, 'view.html'), data, os.path.join(dpath, 'view.html')) 
        