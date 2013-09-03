import os
from uliweb import settings
from uliweb.contrib.upload import FileServing, UUIDFilenameConverter
from uliweb.orm import get_model
from uliweb.i18n import ugettext as _

class DBFileServing(FileServing):
    def __init__(self, default_filename_converter_cls=UUIDFilenameConverter):
        super(DBFileServing, self).__init__(default_filename_converter_cls=default_filename_converter_cls)
        self.model = get_model('dbuploadfiles')
        
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
        
        return nfile
    
    def get_file_record(self, fileid):
        from uliweb import error
        
        obj = self.model.get(self.model.c.slug==fileid)
        if not obj:
            error(_('File %s is not found!') % fileid)
        return obj
    
    def download(self, filename, action=None, x_filename='', real_filename=''):
        """
        action will be "download", "inline"
        and if the request.GET has 'action', then the action will be replaced by it.
        """
        from uliweb.utils.common import safe_str
        from uliweb.utils.filedown import filedown
        from uliweb import request
        from StringIO import StringIO
        from uliweb.utils import files
        
        action = request.GET.get('action', action)
        
        fname = safe_str(filename)
        if not x_filename:
            x_filename = fname
        if self.x_file_prefix:
            x_filename = os.path.normpath(os.path.join(self.x_file_prefix, x_filename)).replace('\\', '/')
        
        if not real_filename:
            #if not real_filename, then get the file info from database
            obj = self.get_file_record(filename)
            fname = obj.filename.encode('utf8')
            fileobj = StringIO(obj.content), obj.create_time, obj.size
            #fileobj should be (filename, mtime, size)
        else:
            fileobj = None
            s = settings.GLOBAL
            real_filename = files.encode_filename(real_filename, to_encoding=s.FILESYSTEM_ENCODING)
        
        return filedown(request.environ, fname, action=action, 
            x_sendfile=bool(self.x_sendfile), x_header_name=self.x_header_name, 
            x_filename=x_filename, real_filename=real_filename, fileobj=fileobj)
     
    def save_file(self, filename, fobj, replace=False, convert=True):
        path, _f = os.path.split(filename)
        #get full path and converted filename
        fname = self.get_filename(_f, True, convert=convert)
        #save file to database
        text = fobj.read()
        obj = self.model(filename=_f, content=text, size=len(text), slug=fname, path=path)
        obj.save()
        
        return fname
    
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
        obj = self.get_file_record(filename)
        obj.delete()
    
    def get_url(self, filename, query_para=None, **url_args):
        """
        Return <a href="filename" title="filename"> tag
        You should pass title and text to url_args, if not pass, then using filename
        """
        from uliweb.core.html import Tag
        
        obj = self.get_file_record(filename)
        title = url_args.pop('title', obj.filename)
        text = url_args.pop('text', title)
        query_para = query_para or {}
        return str(Tag('a', title, href=self.get_href(filename, **query_para), **url_args))
        