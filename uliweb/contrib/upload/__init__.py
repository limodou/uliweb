import os
from uliweb.core.dispatch import bind
from uliweb.core.SimpleFrame import expose
from werkzeug.exceptions import Forbidden

__all__ = ['save_file', 'get_filename', 'get_url', 'save_file_field', 'save_image_field', 
    'delete_filename', 'normfilename']

#@bind('startup_installed')
#def install(sender):
#    url = sender.settings.UPLOAD.URL_SUFFIX.rstrip('/')
#    expose('%s/<path:filename>' % url, static=True)(file_serving)
    
class FileServing(object):
    options = {
        'x_sendfile' : ('UPLOAD/X_SENDFILE', None),
        'x_header_name': ('UPLOAD/X_HEADER_NAME', ''),
        'x_file_prefix': ('UPLOAD/X_FILE_PREFIX', '/files'),
    }
    
    def __init__(self):
        from uliweb import settings
        
        for k, v in self.options.items():
            item, default = v
            setattr(self, k, settings.get_var(item, default))
            
        if self.x_sendfile and not self.x_header_name:
            if self.x_sendfile == 'nginx':
                self.x_header_name = 'X-Accel-Redirect'
            elif self.x_sendfile == 'apache':
                self.x_header_name = 'X-Sendfile'
            else:
                raise Exception, "X_HEADER can't be None, or X_SENDFILE is not supprted"
        
    def do(self, filename, action=None, x_filename='', real_filename=''):
        """
        action will be "download", "inline"
        and if the request.GET has 'action', then the action will be replaced by it.
        """
        from uliweb.utils.common import safe_str
        from uliweb.utils.filedown import filedown
        from uliweb import request
        
        action = request.GET.get('action', action)
        
        fname = safe_str(filename)
        if not x_filename:
            x_filename = fname
        if self.x_file_prefix:
            x_filename = os.path.normpath(os.path.join(self.x_file_prefix, x_filename)).replace('\\', '/')
        
        return filedown(request.environ, fname, action=action, 
            x_sendfile=bool(self.x_sendfile), x_header_name=self.x_header_name, 
            x_filename=x_filename, real_filename=real_filename)
     
def file_serving(filename):
    f = FileServing()
    return f.do(filename)

#def file_serving(filename, action=None, x_sendfile=None, x_header_name=None, 
#    x_file_prefix=None, x_filename=None, real_filename=None):
#    """
#    if url_filename is not given, then it means the url filename should be the same
#        with filename
#    """
#    from uliweb import settings, request
#    from uliweb.utils.filedown import filedown
#    from uliweb.utils import files
#    
#    s = settings.GLOBAL
#    fname = files.encode_filename(filename, s.HTMLPAGE_ENCODING, s.HTMLPAGE_ENCODING)
#    x_filename = x_filename or fname
#    action = request.GET.get('action', action)
#    if x_sendfile is None:
#        x_sendfile = settings.get_var('UPLOAD/X_SENDFILE')
#    if x_header_name is None:
#        x_header_name = settings.get_var('UPLOAD/X_HEADER_NAME')
#    if x_file_prefix is None:
#        x_file_prefix = settings.get_var('UPLOAD/X_FILE_PREFIX')
#    if x_file_prefix:
#        x_filename = os.path.normpath(os.path.join(x_file_prefix, x_filename)).replace('\\', '/')
#    
#    return filedown(request.environ, fname, action=action, 
#        x_sendfile=bool(x_sendfile), x_header_name=x_header_name, x_filename=x_filename, 
#        real_filename=real_filename)

def normfilename(filename):
    return os.path.normpath(filename).replace('\\', '/')
    
def get_filename(filename, filesystem=False):
    from uliweb import application
    from uliweb.utils import files
    from uliweb.utils.common import safe_unicode
    
    #make sure the filename is unicode
    s = application.settings.GLOBAL
    filename = safe_unicode(filename, s.HTMLPAGE_ENCODING)
    
    path = os.path.normpath(application.settings.UPLOAD.TO_PATH).replace('\\', '/')
    f = os.path.normpath(os.path.join(path, filename)).replace('\\', '/')
    if not f.startswith(path):
        raise Forbidden("You can not visit unsafe files.")
    if filesystem:
        return files.encode_filename(f, s.HTMLPAGE_ENCODING, s.FILESYSTEM_ENCODING)
    return f

def save_file(filename, fobj, replace=False):
    from uliweb import application
    from uliweb.utils import files
    
    assert hasattr(fobj, 'read'), "fobj parameter should be a file-like object"
    #get full path filename
    fname = get_filename(filename)
    s = application.settings.GLOBAL
    
    #change full path filename to filesystem filename
    fname1 = files.encode_filename(fname, s.HTMLPAGE_ENCODING, s.FILESYSTEM_ENCODING)
    
    #save file and get the changed filename, because the filename maybe change when
    #there is duplicate filename(replace=False, if replace=True, then the filename
    #will not changed
    fname2 = files.save_file(fname1, fobj, replace, application.settings.UPLOAD.BUFFER_SIZE)
    
    #create new filename according fname2 and filename, the result should be unicode
    return normfilename(os.path.join(os.path.dirname(filename), files.unicode_filename(fname2, s.FILESYSTEM_ENCODING)))

def save_file_field(field, replace=False, filename=None):
    assert field
    filename = filename or field.data.filename
    fname = save_file(filename, field.data.file, replace)
    field.data.filename = fname
    return fname
        
def save_image_field(field, resize_to=None, replace=False, filename=None):
    assert field
    if resize_to:
        from uliweb.utils.image import resize_image
        field.data.file = resize_image(field.data.file, resize_to)
    filename = filename or field.data.filename
    fname = save_file(filename, field.data.file, replace)
    field.data.filename = fname
    return fname
        
def delete_filename(filename):
    f = get_filename(filename, filesystem=True)
    if os.path.exists:
        os.remove(f)

def get_url(filename):
    import urllib
    from uliweb import application

    if not filename:
        return ''
    
    #make sure the filename is utf-8 encoded
    if isinstance(filename, unicode):
        filename = filename.encode('utf-8')
#    filename = urllib.quote_plus(filename)
    fname = os.path.normpath(filename)
    f = normfilename(os.path.join(application.settings.UPLOAD.URL_SUFFIX, fname))
    
    return f
