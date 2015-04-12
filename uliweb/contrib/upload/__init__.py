import os
from uliweb import settings, url_for
from uliweb.utils import files
from uliweb.utils.common import import_attr, application_path, log
import random
import time

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
                                      os.getpid())).hexdigest(), 
                ).hexdigest()
        
        return f + ext
    
class FileServing(object):
    default_config = 'UPLOAD'
    options = {
        'x_sendfile' : ('X_SENDFILE', None),
        'x_header_name': ('X_HEADER_NAME', ''),
        'x_file_prefix': ('X_FILE_PREFIX', '/files'),
        'to_path': ('TO_PATH', './uploads'),
        'buffer_size': ('BUFFER_SIZE', 4096),
        '_filename_converter': ('FILENAME_CONVERTER', None),
    }
    
    def __init__(self, default_filename_converter_cls=UUIDFilenameConverter, config=None):
        self.config = config or self.default_config
        for k, v in self.options.items():
            item, default = v
            #if there is no '/' in option, then combine config with option
            #else assume the option is just like 'SECTION/OPTION', then skip it
            if '/' not in item:
                item = self.config + '/' + item
            value = settings.get_var(item, default)
            setattr(self, k, value)
            
        if self.x_sendfile and not self.x_header_name:
            if self.x_sendfile == 'nginx':
                self.x_header_name = 'X-Accel-Redirect'
            elif self.x_sendfile == 'apache':
                self.x_header_name = 'X-Sendfile'
            else:
                raise Exception("X_HEADER can't be None, or X_SENDFILE is not supprted")
        if isinstance(self._filename_converter, (str, unicode)):
            self._filename_converter_cls = import_attr(self._filename_converter)
        else:
            self._filename_converter_cls = self._filename_converter or default_filename_converter_cls
        
    def filename_convert(self, filename, convert_cls=None):
        convert_cls = convert_cls or self._filename_converter_cls
        return convert_cls.convert(filename)
        
    def get_filename(self, filename, filesystem=False, convert=False, subpath=''):
        """
        Get the filename according to self.to_path, and if filesystem is False
        then return unicode filename, otherwise return filesystem encoded filename
    
        @param filename: relative filename, it'll be combine with self.to_path
        @param filesystem: if True, then encoding the filename to filesystem
        @param convert: if True, then convert filename with FilenameConverter class
        @param subpath: sub folder in to_path
        """
        from uliweb.utils.common import safe_unicode
        
        #make sure the filename is unicode
        s = settings.GLOBAL
        if convert:
            _p, _f = os.path.split(filename)
            _filename = os.path.join(_p, self.filename_convert(_f))
        else:
            _filename = filename
        nfile = safe_unicode(_filename, s.HTMLPAGE_ENCODING)

        if subpath:
            paths = [application_path(self.to_path), subpath, nfile]
        else:
            paths = [application_path(self.to_path), nfile]
        f = os.path.normpath(os.path.join(*paths)).replace('\\', '/')
    
        if filesystem:
            return files.encode_filename(f, to_encoding=s.FILESYSTEM_ENCODING)
        return f

    def download(self, filename, action='download', x_filename='', x_sendfile=None, real_filename=''):
        """
        action will be "download", "inline"
        and if the request.GET has 'action', then the action will be replaced by it.
        """
        from uliweb import request
        from uliweb.utils.common import safe_str
        from uliweb.utils.filedown import filedown
        
        s = settings.GLOBAL

        action = request.GET.get('action', action)
        
        if not real_filename:
            real_filename = self.get_filename(filename, True, convert=False)
        else:
            real_filename = files.encode_filename(real_filename, to_encoding=s.FILESYSTEM_ENCODING)

        if not x_filename:
            x_filename = safe_str(filename, s.FILESYSTEM_ENCODING)
        if self.x_file_prefix:
            x_filename = os.path.normpath(os.path.join(self.x_file_prefix, x_filename)).replace('\\', '/')
        
        xsend_flag = bool(self.x_sendfile) if x_sendfile is None else x_sendfile
        return filedown(request.environ, filename, action=action, 
            x_sendfile=xsend_flag, x_header_name=self.x_header_name, 
            x_filename=x_filename, real_filename=real_filename)
     
    def save_file(self, filename, fobj, replace=False, convert=True, subpath=''):
        from uliweb.utils import files
        
        #get full path and converted filename
        fname = self.get_filename(filename, True, convert=convert, subpath=subpath)
        #save file and get the changed filename, because the filename maybe change when
        #there is duplicate filename, if replace=True, then the filename
        #will not changed
        fname2 = files.save_file(fname, fobj, replace, self.buffer_size)
        
        s = settings.GLOBAL
        #create new filename according fname2 and filename, the result should be unicode
        return norm_filename(os.path.join(os.path.dirname(filename), files.unicode_filename(fname2, s.FILESYSTEM_ENCODING)))
    
    def save_file_field(self, field, replace=False, filename=None, convert=True, subpath=''):
        filename = filename or field.data.filename
        fname = self.save_file(filename, field.data.file, replace, convert, subpath=subpath)
        field.data.filename = fname
        return fname
            
    def save_image_field(self, field, resize_to=None, replace=False, filename=None,
                         convert=True, subpath=''):
        from uliweb.utils.image import resize_image
        if resize_to:
            field.data.file = resize_image(field.data.file, resize_to)
        filename = filename or field.data.filename
        fname = self.save_file(filename, field.data.file, replace, convert, subpath=subpath)
        field.data.filename = fname
        return fname
            
    def delete_filename(self, filename, subpath=''):
        f = self.get_filename(filename, filesystem=True, convert=False, subpath=subpath)
        if os.path.exists(f):
            try:
                os.unlink(f)
            except Exception as e:
                log.exception(e)
    
    def get_href(self, filename, **kwargs):
        if not filename:
            return ''

        s = settings.GLOBAL
        fname = norm_filename(files.unicode_filename(filename, s.FILESYSTEM_ENCODING))
        f = url_for('file_serving', filename=fname, **kwargs)
        return f
        
    def get_url(self, filename, query_para=None, **url_args):
        """
        Return <a href="filename" title="filename"> tag
        You should pass title and text to url_args, if not pass, then using filename
        """
        from uliweb.core.html import Tag
        
        title = url_args.pop('title', filename)
        text = url_args.pop('text', title)
        query_para = query_para or {}
        return str(Tag('a', title, href=self.get_href(filename, **query_para), **url_args))

def get_backend(config=None):
    global default_fileserving
    
    if default_fileserving and not config:
        return default_fileserving
    else:
        config = config or 'UPLOAD'
        cls = settings.get_var('%s/BACKEND' % config)
        if cls:
            fileserving = import_attr(cls)(config=config)
        else:
            fileserving = FileServing(config=config)
        if config == 'UPLOAD':
            default_fileserving = fileserving
        return fileserving

get_fileserving = get_backend

def file_serving(filename, action='download', real_filename=None, x_sendfile=None, x_filename=None):
    from uliweb import request
    import urllib2
    
    alt_filename = request.GET.get('alt')
    if not alt_filename:
        alt_filename = filename
    else:
        alt_filename = urllib2.unquote(alt_filename)
    if not real_filename:
        _filename = get_filename(filename, False, convert=False)
    else:
        _filename = real_filename
    if not x_filename:
        x_filename = filename
    return get_backend().download(alt_filename, action=action, real_filename=_filename, x_sendfile=x_sendfile, x_filename=x_filename)

def filename_convert(filename, convert_cls=None):
    return get_backend().filename_convert(filename, convert_cls=convert_cls)

def get_filename(filename, filesystem=False, convert=False, subpath=''):
    return get_backend().get_filename(filename, filesystem, convert=convert, subpath=subpath)

def save_file(filename, fobj, replace=False, convert=True, subpath=''):
    return get_backend().save_file(filename, fobj, replace, convert, subpath=subpath)
    
def save_file_field(field, replace=False, filename=None, convert=True, subpath=''):
    return get_backend().save_file_field(field, replace, filename, convert, subpath=subpath)
        
def save_image_field(field, resize_to=None, replace=False, filename=None, convert=True, subpath=''):
    return get_backend().save_image_field(field, resize_to, replace, filename, convert, subpath=subpath)
        
def delete_filename(filename):
    return get_backend().delete_filename(filename)

def get_url(filename, query_para=None, **url_args):
    return get_backend().get_url(filename, query_para, **url_args)

def get_href(filename, *args, **kwargs):
    return get_backend().get_href(filename, *args, **kwargs)

def download(filename, *args, **kwargs):
    return get_backend().download(filename, *args, **kwargs)

def after_init_apps(sender):
    import mimetypes
    from uliweb import settings
    
    for k, v in settings.get('MIME_TYPES').items():
        if not k.startswith('.'):
            k = '.' + k
        mimetypes.add_type(v, k)
