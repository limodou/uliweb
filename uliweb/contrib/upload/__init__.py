import os
from uliweb.core.dispatch import bind
from uliweb.core.SimpleFrame import expose
from werkzeug.exceptions import Forbidden

__all__ = ['save_file', 'get_filename', 'get_url', 'save_file_field', 'save_image_field', 
    'delete_filename', 'normfilename']

@bind('startup_installed')
def install(sender):
    url = sender.settings.UPLOAD.URL_SUFFIX.rstrip('/')
    expose('%s/<path:filename>' % url, static=True)(file_serving)
 
def file_serving(filename):
    from uliweb.utils.filedown import filedown
    from uliweb.core.SimpleFrame import local
    
    fname = get_filename(filename, filesystem=True)
    action = request.GET.get('action', 'download')
    if action == 'inline':
        return filedown(local.request.environ, fname, inline=True)
    else:
        return filedown(local.request.environ, fname, download=True)

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
