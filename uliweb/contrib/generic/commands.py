import os
from uliweb.core.commands import Command
from optparse import make_option

class GenericCommand(Command):
    name = 'generic'
    option_list = (
        make_option('-a', '--appname', dest='appname', help='App name.'),
        make_option('-t', '--tablename', dest='tablename', help='Table name.'),
        make_option('-c', '--classname', dest='classname', help='Class name.'),
        make_option('--viewfile', dest='viewfile', help='View file name.'),
        make_option('-u', '--url', dest='url', help='Class View URL prefix.'),
        make_option('--theme', dest='theme', help='theme name, available themes is [a-angularjs].'),
    )
    help = 'Create a scaffold for an generic admin interface.'
    args = ''
    check_apps_dirs = False
    has_options = True
    check_apps = False
    
    def get_input(self, prompt, default=None, choices=None, option_value=None):
        if option_value:
            return option_value
        
        choices = choices or []
        r = raw_input(prompt+' ') or default
        while 1:
            if not r:
                r = raw_input(prompt)
            if choices:
                if r not in choices:
                    r = None
                else:
                    break
            else:
                break
        return r
    
    def handle(self, options, global_options, *args):
        d = {}
        d['appname'] = self.get_input("Appname:", option_value=options.appname)
        d['tablename'] = self.get_input("Table Name:", option_value=options.tablename)
        view_name = d['tablename'].capitalize()+'View'
        view_file_name = 'views_%s.py' % d['tablename']
        url_prefix = '/'+d['appname']
        d['classname'] = self.get_input("View Class Name [%s]:" % view_name, default=view_name, option_value=options.classname)
        d['viewfile'] = self.get_input("Save views to [%s]:" % view_file_name, default=view_file_name, option_value=options.viewfile)
        d['url'] = self.get_input("Class View URL prefix [%s]:" % url_prefix, default=url_prefix, option_value=options.url)
        d['theme'] = self.get_input("Creation Theme([a]ngularjs):", default="a", choices=['a'], option_value=options.theme)
        
        theme = {'a':'angularjs'}
        
        func = getattr(self, 'process_'+theme.get(d['theme']))
        func(d, options, global_options, args)
        
    def process_angularjs(self, data, options, global_options, args):
        from uliweb.utils.common import pkg, copy_dir
        from uliweb.core.template import template_file
        import shutil
        
        #if there is no apps/appname then create files in current directory
        
        path = os.path.join(global_options.apps_dir, data['appname'])
        if not os.path.exists(path):
            path = '.'
            
        gpath = pkg.resource_filename('uliweb.contrib.generic', 'template_files/angularjs')
        
        #process view file
        view_text = template_file(os.path.join(gpath, 'views.py'), data)
        view_file = os.path.join(path, data['viewfile'])
        if os.path.exists(view_file):
            if os.path.getsize(view_file) == 0:
                view_text = '#coding=utf8\n' + view_text
            f = open(view_file, 'a')
        else:
            view_text = '#coding=utf8\n' + view_text
            f = open(view_file, 'w')
        f.write(view_text)
        f.close()
        
        def render(fpath, dst, df):
            text = template_file(fpath, data)
            open(df, 'w').write(text)
            return True
        
        #process templates
        copy_dir(os.path.join(gpath, 'templates'), os.path.join(path, 'templates', data['classname']),
            processor=render)

        #process config.ini
        shutil.copy2(os.path.join(gpath, 'config.ini'), path)