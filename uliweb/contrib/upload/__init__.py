import os
from uliweb import settings, request, url_for
from uliweb.utils import files

__all__ = ['save_file', 'get_filename', 'get_url', 'save_file_field', 'save_image_field', 
    'delete_filename', 'norm_filename']

def norm_filename(filename):
    return os.path.normpath(filename).replace('\\', '/')
    
class FileServing(object):
    options = {
        'x_sendfile' : ('UPLOAD/X_SENDFILE', None),
        'x_header_name': ('UPLOAD/X_HEADER_NAME', ''),
        'x_file_prefix': ('UPLOAD/X_FILE_PREFIX', '/files'),
        'to_path': ('UPLOAD/TO_PATH', './uploads'),
        'buffer_size': ('UPLOAD/BUFFER_SIZE', 4096),
    }
    
    def __init__(self):
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
        
    def get_filename(self, filename, filesystem=False):
        """
        Get the filename according to self.to_path, and if filesystem is False
        then return unicode filename, otherwise return filesystem encoded filename
        """
        from uliweb.utils.common import safe_unicode
        
        #make sure the filename is unicode
        s = settings.GLOBAL
        filename = safe_unicode(filename, s.HTMLPAGE_ENCODING)
        
        f = os.path.normpath(os.path.join(self.to_path, filename)).replace('\\', '/')
    
        if filesystem:
            return files.encode_filename(f, to_encoding=s.FILESYSTEM_ENCODING)
        return f

    def download(self, filename, action=None, x_filename='', real_filename=''):
        """
        action will be "download", "inline"
        and if the request.GET has 'action', then the action will be replaced by it.
        """
        from uliweb.utils.common import safe_str
        from uliweb.utils.filedown import filedown
        
        action = request.GET.get('action', action)
        
        fname = safe_str(filename)
        if not x_filename:
            x_filename = fname
        if self.x_file_prefix:
            x_filename = os.path.normpath(os.path.join(self.x_file_prefix, x_filename)).replace('\\', '/')
        
        if not real_filename:
            real_filename = self.get_filename(filename, True)
        else:
            s = settings.GLOBAL
            real_filename = files.encode_filename(real_filename, to_encoding=s.FILESYSTEM_ENCODING)
        
        return filedown(request.environ, fname, action=action, 
            x_sendfile=bool(self.x_sendfile), x_header_name=self.x_header_name, 
            x_filename=x_filename, real_filename=real_filename)
     
    def save_file(self, filename, fobj, replace=False):
        from uliweb.utils import files
        
        assert hasattr(fobj, 'read'), "fobj parameter should be a file-like object"
        #get full path filename
        fname = self.get_filename(filename, True)
        #save file and get the changed filename, because the filename maybe change when
        #there is duplicate filename(replace=False, if replace=True, then the filename
        #will not changed
        fname2 = files.save_file(fname, fobj, replace, self.buffer_size)
        
        s = settings.GLOBAL
        #create new filename according fname2 and filename, the result should be unicode
        return norm_filename(os.path.join(os.path.dirname(filename), files.unicode_filename(fname2, s.FILESYSTEM_ENCODING)))
    
    def save_file_field(self, field, replace=False, filename=None):
        filename = filename or field.data.filename
        fname = self.save_file(filename, field.data.file, replace)
        field.data.filename = fname
        return fname
            
    def save_image_field(self, field, resize_to=None, replace=False, filename=None):
        from uliweb.utils.image import resize_image
        if resize_to:
            field.data.file = resize_image(field.data.file, resize_to)
        filename = filename or field.data.filename
        fname = self.save_file(filename, field.data.file, replace)
        field.data.filename = fname
        return fname
            
    def delete_filename(self, filename):
        f = self.get_filename(filename, filesystem=True)
        if os.path.exists:
            os.remove(f)
    
    def get_url(self, filename):
        if not filename:
            return ''
        
        #make sure the filename is utf-8 encoded
        s = settings.GLOBAL
        fname = files.unicode_filename(filename, s.FILESYSTEM_ENCODING)
        f = norm_filename(url_for('file_serving', filename=fname))
        
        return f
    
default_fileserving = FileServing()

def file_serving(filename):
    return default_fileserving.download(filename)

def get_filename(filename, filesystem=False):
    return default_fileserving.get_filename(filename, filesystem)

def save_file(filename, fobj, replace=False):
    return default_fileserving.save_file(filename, fobj, replace)
    
def save_file_field(field, replace=False, filename=None):
    return default_fileserving.save_file_field(filename, replace, filename)
        
def save_image_field(field, resize_to=None, replace=False, filename=None):
    return default_fileserving.save_image_field(filename, resize_to, replace, filename)
        
def delete_filename(filename):
    return default_fileserving.delete_filename(filename)

def get_url(filename):
    return default_fileserving.get_url(filename)
