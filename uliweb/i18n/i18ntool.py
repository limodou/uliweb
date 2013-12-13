import os
from optparse import make_option
from uliweb.core import SimpleFrame
from uliweb.utils.common import pkg
from uliweb.core.commands import Command

#def getfiles(path):
#    files_list = []
#    if os.path.exists(os.path.abspath(os.path.normpath(path))):
#        if os.path.isfile(path):
#            files_list.append(path)
#        else:
#            for root, dirs, files in os.walk(path):
#                for f in files:
#                    filename = os.path.join(root, f)
#                    if '.svn' in filename or (not filename.endswith('.py') and not filename.endswith('.html') and not filename.endswith('.ini')):
#                        continue
#                    files_list.append(filename)
#    return files_list

def _get_outputfile(path, locale='en'):
    output = os.path.normpath(os.path.join(path, 'locale', locale, 'LC_MESSAGES', 'uliweb.pot'))
    return output

def _process(path, locale, options, output_dir=None):
    from pygettext import extrace_files
    from po_merge import merge
    from uliweb.utils import pyini

    output_dir = output_dir or path
    output = _get_outputfile(output_dir, locale=locale)
    try:
        if options['template']:
            x = pyini.Ini(options['template'])
        else:
            x = pyini.Ini()
        vars = {}
        vars['First_Author'] = x.get_var('I18N/First_Author', 'FIRST AUTHOR <EMAIL@ADDRESS>')
        vars['Project_Id_Version'] = x.get_var('I18N/Project_Id_Version', 'PACKAGE VERSION')
        vars['Last_Translator'] = x.get_var('I18N/Last_Translator', 'FULL NAME <EMAIL@ADDRESS>')
        vars['Language_Team'] = x.get_var('I18N/Language_Team', 'LANGUAGE <LL@li.org>')
        vars['Content_Type_Charset'] = x.get_var('I18N/Content_Type_Charset', 'utf-8')
        vars['Content_Transfer_Encoding'] = x.get_var('I18N/Content_Transfer_Encoding', '8bit')
        vars['Plural_Forms'] = x.get_var('I18N/Plural_Forms', 'nplurals=1; plural=0;')
        
        extrace_files(path, output, {'verbose':options['verbose']}, vars=vars)
        print 'Success! output file is %s' % output
        merge(output[:-4]+'.po', output, options['exact'])
    except:
        raise
 
class I18nCommand(Command):
    name = 'i18n'
    check_apps_dirs = False
    args = '<appname, appname, ...>'
    help = 'Extract i18n message catalog form app or all apps. Please notice that you can not set -p, -d, --uliweb, --apps and <appname, ...> at the same time.'
    has_options = True
    option_list = (
        make_option('--apps', dest='apps', action='store_true', default=False,
            help='If set, then extract translation messages from all apps located in project direcotry, and save .po file in each app direcotry.'),
        make_option('-p', dest='project', action='store_true', default=False,
            help='If set, then extract translation messages from project directory.'),
        make_option('-d', dest='directory', 
            help='If set, then extract translation messages from directory.'),
        make_option('--uliweb', dest='uliweb', action='store_true', default=False,
            help='If set, then extract translation messages from uliweb.'),
        make_option('-l', dest='locale', default='en',
            help='Target locale. Default is "en".'),
        make_option('--exact', dest='exact', action='store_true', default=False,
            help='If set, then all entries existed in old .po file but not existed in new .pot will be removed.'),
        make_option('-t', '--template', dest='template',
            help='PO variables definition, such as: charset, translater, etc.'),
    )
    
    def handle(self, options, global_options, *args):
        from uliweb.utils.common import check_apps_dir
        opts = {'verbose':global_options.verbose, 'template':options.template,
            'exact':options.exact}
        if options.project:
            check_apps_dir(global_options.apps_dir)
            app = self.get_application(global_options)
            
            _process(global_options.apps_dir, options.locale, opts, output_dir=global_options.project)
        elif options.apps or args:
            check_apps_dir(global_options.apps_dir)
            
            app = self.get_application(global_options)
            if options.apps:
                _apps = SimpleFrame.get_apps(global_options.apps_dir)
            else:
                _apps = args
            apps_dir = os.path.normpath(os.path.abspath(global_options.apps_dir))
            for appname in _apps:
                path = SimpleFrame.get_app_dir(appname)
                if global_options.verbose:
                    print 'Processing... app=>[%s] path=>[%s]' % (appname, path)
                _process(path, options.locale, opts)
        elif options.uliweb:
            path = pkg.resource_filename('uliweb', '')
            _process(path, options.locale, opts)
        elif options.directory:
            _process(options.directory, options.locale, opts)
            
