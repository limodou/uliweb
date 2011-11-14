import os
from uliweb import settings, request, url_for
from uliweb.utils import files
from uliweb.utils.common import import_attr

__all__ = ['save_file', 'get_filename', 'get_url', 'save_file_field', 'save_image_field', 
    'delete_filename', 'norm_filename']

default_fileserving = None

def norm_filename(filename):
    return os.path.normpath(filename).replace('\\', '/')

class FilenameConverter(object):
    @staticmethod
    def convert(filename):
        return filename
    
class UUIDFilenameConverter(object):
    @staticmethod
    def convert(filename):
        import uuid
        _f, ext = os.path.splitext(filename)
        return uuid.uuid1().hex + ext
    
class MD5FilenameConverter(object):
    @staticmethod
    def convert(filename):
        try:
            from hashlib import md5
        except ImportError:
            from md5 import md5

        _f, ext = os.path.splitext(filename)
        f = md5(
                    md5("%f%s%f%s" % (time.time(), id({}), random.random(),
                                      getpid())).hexdigest(), 
                ).hexdigest()
        
        return f + ext
    
class FileServing(object):
    options = {
        'x_sendfile' : ('UPLOAD/X_SENDFILE', None),
        'x_header_name': ('UPLOAD/X_HEADER_NAME', ''),
        'x_file_prefix': ('UPLOAD/X_FILE_PREFIX', '/files'),
        'to_path': ('UPLOAD/TO_PATH', './uploads'),
        'buffer_size': ('UPLOAD/BUFFER_SIZE', 4096),
        '_filename_converter': ('UPLOAD/FILENAME_CONVERTER', None),
    }
    
    def __init__(self, default_filename_converter_cls=UUIDFilenameConverter):
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
        if isinstance(self._filename_converter, (str, unicode)):
            self._filename_converter_cls = import_attr(self._filename_converter)
        else:
            self._filename_converter_cls = self._filename_converter or default_filename_converter_cls
        
    def filename_convert(self, filename):
        return self._filename_converter_cls.convert(filename)
        
    def get_filename(self, filename, filesystem=False, convert=False):
        """
        Get the filename according to self.to_path, and if filesystem is False
        then return unicode filename, otherwise return filesystem encoded filename
    
        @param filename: relative filename, it'll be combine with self.to_path
        @param filesystem: if True, then encoding the filename to filesystem
        @param convert: if True, then convert filename with FilenameConverter class
        """
        from uliweb.utils.common import safe_unicode
        
        #make sure the filename is unicode
        s = settings.GLOBAL
        if convert:
            _p, _f = os.path.split(filename)
            _filename = os.path.join(_p, self.filename_convert(filename))
        else:
            _filename = filename
        nfile = safe_unicode(_filename, s.HTMLPAGE_ENCODING)
        
        f = os.path.normpath(os.path.join(self.to_path, nfile)).replace('\\', '/')
    
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
            real_filename = self.get_filename(filename, True, convert=False)
        else:
            s = settings.GLOBAL
            real_filename = files.encode_filename(real_filename, to_encoding=s.FILESYSTEM_ENCODING)
        
        return filedown(request.environ, fname, action=action, 
            x_sendfile=bool(self.x_sendfile), x_header_name=self.x_header_name, 
            x_filename=x_filename, real_filename=real_filename)
     
    def save_file(self, filename, fobj, replace=False):
        from uliweb.utils import files
        
        #get full path and converted filename
        fname = self.get_filename(filename, True, convert=True)
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
        f = self.get_filename(filename, filesystem=True, convert=False)
        if os.path.exists:
            os.unlink(f)
    
    def get_href(self, filename):
        if not filename:
            return ''

        s = settings.GLOBAL
        fname = norm_filename(files.unicode_filename(filename, s.FILESYSTEM_ENCODING))
        f = url_for('file_serving', filename=fname)
        return f
        
    def get_url(self, filename, **url_args):
        """
        Return <a href="filename" title="filename"> tag
        You should pass title and text to url_args, if not pass, then using filename
        """
        from uliweb.core.html import Tag
        
        title = url_args.pop('title', filename)
        text = url_args.pop('text', title)
        return str(Tag('a', title, href=self.get_href(filename), **url_args))

def get_backend():
    global default_fileserving
    
    if default_fileserving:
        return default_fileserving
    else:
        cls = settings.get_var('UPLOAD/BACKEND')
        if cls:
            default_fileserving = import_attr(cls)()
        else:
            default_fileserving = FileServing()
        return default_fileserving

def file_serving(filename):
    return get_backend().download(filename)

def get_filename(filename, filesystem=False):
    return get_backend().get_filename(filename, filesystem)

def save_file(filename, fobj, replace=False):
    return get_backend().save_file(filename, fobj, replace)
    
def save_file_field(field, replace=False, filename=None):
    return get_backend().save_file_field(field, replace, filename)
        
def save_image_field(field, resize_to=None, replace=False, filename=None):
    return get_backend().save_image_field(field, resize_to, replace, filename)
        
def delete_filename(filename):
    return get_backend().delete_filename(filename)

def get_url(filename, **url_args):
    return get_backend().get_url(filename, **url_args)

def get_href(filename):
    return get_backend().get_href(filename)
